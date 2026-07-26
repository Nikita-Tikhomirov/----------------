import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.monitor_mail_dns import evaluate_dns_target


TARGET = {
    "id": "mchs-spb-mail",
    "domain": "mchs-spb.ru",
    "expected_mx": ["emx.mail.ru"],
    "spf_required": ["include:beget.com", "include:_spf.mail.ru"],
    "dkim": {"name": "beget._domainkey.mchs-spb.ru", "required": ["v=DKIM1", "p="]},
}


def records(mx=None, spf=None, dkim=None):
    return {
        "mx": mx or ["10 emx.mail.ru."],
        "spf": spf or ["v=spf1 include:beget.com include:_spf.mail.ru ~all"],
        "dkim": dkim or ["v=DKIM1; k=rsa; p=abc"],
    }


def test_expected_mail_dns_records_are_healthy():
    result = evaluate_dns_target(TARGET, records())

    assert result["healthy"] is True
    assert result["issues"] == []


def test_missing_expected_mx_is_reported():
    result = evaluate_dns_target(TARGET, records(mx=["10 mx1.beget.com."]))

    assert result["healthy"] is False
    assert result["issues"] == ["missing MX target: emx.mail.ru"]


def test_missing_dkim_marker_is_reported():
    result = evaluate_dns_target(TARGET, records(dkim=["v=DKIM1; k=rsa;"]))

    assert result["healthy"] is False
    assert result["issues"] == ["DKIM is missing required marker: p="]
