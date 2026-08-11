from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_expected_recipient_contract_has_all_30_included_sites():
    from tools.verify_apreal_recipient_matrix import expected_recipients

    routes = expected_recipients()

    assert len(routes) == 30
    assert routes["apreal.ru"] == "info@apreal.ru"
    assert routes["apreal.spb.ru"] == "spb@apreal.ru"
    assert routes["apreal-volgograd.ru"] == "vlg-ap@bk.ru"
    assert routes["nousro-spb.ru"] == "spb@nousro.ru"
    assert routes["shopap.ru"] == "info@shopap.ru"
    assert "lic-k.ru" not in routes
    assert "apreal-samara.ru" not in routes


def test_php_recipient_parser_handles_standard_and_custom_handlers():
    from tools.verify_apreal_recipient_matrix import extract_php_recipient

    assert (
        extract_php_recipient("const CSF_RECIPIENT = 'info@example.ru';")
        == "info@example.ru"
    )
    assert (
        extract_php_recipient("$sent = wp_mail('forms@example.ru', $subject, $body);")
        == "forms@example.ru"
    )
    assert (
        extract_php_recipient("$sent = mail(\n    'mailbox@example.ru',\n    $subject\n);")
        == "mailbox@example.ru"
    )


def test_matrix_summary_requires_every_check_and_rejects_personal_routes():
    from tools.verify_apreal_recipient_matrix import summarize

    good = [
        {
            "domain": "example.ru",
            "actual_recipient": "info@example.ru",
            "expected_recipient": "info@example.ru",
            "passed": True,
        }
    ]
    bad = [
        *good,
        {
            "domain": "other.ru",
            "actual_recipient": "stithc92@gmail.com",
            "expected_recipient": "info@other.ru",
            "passed": False,
        },
    ]

    assert summarize(good) == {
        "checks": 1,
        "passed": 1,
        "failed": [],
        "personal_recipient_hits": [],
        "complete": True,
    }
    result = summarize(bad)
    assert result["complete"] is False
    assert result["failed"] == ["other.ru"]
    assert result["personal_recipient_hits"] == [
        {"domain": "other.ru", "recipient": "stithc92@gmail.com"}
    ]


def test_known_legacy_cf7_forms_are_included_in_route_audit():
    from tools.verify_apreal_recipient_matrix import legacy_cf7_contracts

    contracts = {
        (item["domain"], item["form_id"], item["expected_recipient"])
        for item in legacy_cf7_contracts()
    }

    assert ("apreal.ru", 6945, "info@apreal.ru") in contracts
    assert ("apreal.spb.ru", 22, "spb@apreal.ru") in contracts
    assert ("mchs78.ru", 63, "info@mchs78.ru") in contracts
    assert ("nousro-spb.ru", 2434, "spb@nousro.ru") in contracts
    assert ("nousro-nn.ru", 3307, "info@nousro-nn.ru") in contracts


def test_recipient_matrix_cli_can_run_as_a_direct_script():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "tools/verify_apreal_recipient_matrix.py", "--help"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Read live AP-Real form recipients" in result.stdout


def test_recipient_matrix_reconnects_after_transport_drop():
    from paramiko.ssh_exception import SSHException

    from tools.verify_apreal_recipient_matrix import collect_checks_with_retries

    connections = []

    class FakeConnection:
        def __init__(self, attempt):
            self.attempt = attempt
            self.closed = False

        def close(self):
            self.closed = True

    def connector(_args):
        connection = FakeConnection(len(connections) + 1)
        connections.append(connection)
        return connection

    def collector(connection):
        if connection.attempt == 1:
            raise SSHException("server connection dropped")
        return [{"domain": "example.ru", "passed": True}]

    checks = collect_checks_with_retries(
        object(),
        connector=connector,
        collector=collector,
        attempts=3,
        retry_delay=0,
    )

    assert checks == [{"domain": "example.ru", "passed": True}]
    assert len(connections) == 2
    assert all(connection.closed for connection in connections)
