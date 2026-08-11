#!/usr/bin/env python3
"""Read live AP-Real form recipients without changing remote state."""

from __future__ import annotations

import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import sys
import time
from typing import Any

from paramiko.ssh_exception import SSHException

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import deploy_apreal_cf7_recipient_normalization as cf7_legacy
from tools import deploy_apreal_custom_form_completion as custom_deploy
from tools import deploy_apreal_standard_family as standard_deploy


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "changes/2026-07-20/build_standard_forms.py"
DEFAULT_OUTPUT = ROOT / "output/ap-real-post-send-recipient-matrix-2026-08-02.json"
REMOTE_HOME = PurePosixPath("/home/n/nousroc9")

CUSTOM_RECIPIENTS = {
    "mca24.ru": "info@mca24.ru",
    "fsa-lab.ru": "info@fsa-lab.ru",
    "med-license.ru": "info@med-license.ru",
    "mhsl.ru": "info@mhsl.ru",
    "apreal36.ru": "info@apreal36.ru",
}

CURRENT_CF7_RECIPIENTS = {
    "apreal.ru": "info@apreal.ru",
    "nousro-spb.ru": "spb@nousro.ru",
}

FORBIDDEN_RECIPIENTS = {
    "stithc92@gmail.com",
    "stithc65@gmail.com",
    "upreal@bk.ru",
    "upreall@yandex.ru",
    "nousro-muc@yandex.ru",
    "admin@admin.com",
}


def _load_generator():
    spec = importlib.util.spec_from_file_location("apreal_standard_forms", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_recipients() -> dict[str, str]:
    generator = _load_generator()
    return {
        **generator.WORDPRESS_SITES,
        **generator.STATIC_SITES,
        **CUSTOM_RECIPIENTS,
        **CURRENT_CF7_RECIPIENTS,
    }


def legacy_cf7_contracts() -> list[dict[str, Any]]:
    return [
        {
            "domain": item.domain,
            "root": item.root,
            "form_id": item.form_id,
            "title": item.title,
            "expected_recipient": item.target_recipient,
        }
        for item in cf7_legacy.RECIPIENT_UPDATES
    ]


def extract_php_recipient(source: str) -> str:
    patterns = (
        r"const\s+CSF_RECIPIENT\s*=\s*['\"]([^'\"]+)['\"]",
        r"\bwp_mail\s*\(\s*['\"]([^'\"]+)['\"]",
        r"\bmail\s*\(\s*['\"]([^'\"]+)['\"]",
    )
    for pattern in patterns:
        match = re.search(pattern, source, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    raise RuntimeError("Recipient was not found in PHP handler")


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sorted({item["domain"] for item in checks if not item.get("passed")})
    personal_hits = [
        {"domain": item["domain"], "recipient": item["actual_recipient"]}
        for item in checks
        if str(item.get("actual_recipient", "")).casefold() in FORBIDDEN_RECIPIENTS
    ]
    passed = sum(bool(item.get("passed")) for item in checks)
    return {
        "checks": len(checks),
        "passed": passed,
        "failed": failed,
        "personal_recipient_hits": personal_hits,
        "complete": bool(checks) and passed == len(checks) and not personal_hits,
    }


def read_remote_file(sftp, path: PurePosixPath) -> str:
    with sftp.open(str(path), "rb") as handle:
        return handle.read().decode("utf-8", "replace")


def file_check(sftp, domain: str, path: PurePosixPath, expected: str, kind: str) -> dict[str, Any]:
    actual = extract_php_recipient(read_remote_file(sftp, path))
    return {
        "domain": domain,
        "kind": kind,
        "source": str(path),
        "actual_recipient": actual,
        "expected_recipient": expected,
        "passed": actual.casefold() == expected.casefold(),
    }


def cf7_check(ssh, contract: dict[str, Any], kind: str) -> dict[str, Any]:
    mail = custom_deploy.get_meta(
        ssh,
        contract["root"],
        int(contract["form_id"]),
        "_mail",
    )
    actual = str(mail.get("recipient", "")).strip()
    expected = str(contract["expected_recipient"])
    return {
        "domain": contract["domain"],
        "kind": kind,
        "source": f"{contract['root']}#form-{contract['form_id']}",
        "form_id": int(contract["form_id"]),
        "title": contract.get("title", ""),
        "actual_recipient": actual,
        "expected_recipient": expected,
        "passed": actual.casefold() == expected.casefold(),
    }


def collect_checks(ssh) -> list[dict[str, Any]]:
    generator = _load_generator()
    checks: list[dict[str, Any]] = []
    with ssh.open_sftp() as sftp:
        for domain, expected in generator.WORDPRESS_SITES.items():
            path = REMOTE_HOME / domain / "public_html/wp-content/mu-plugins/client-standard-forms.php"
            print(f"Reading recipient route: {domain} (wordpress)", file=sys.stderr, flush=True)
            checks.append(file_check(sftp, domain, path, expected, "wordpress_standard"))

        for domain, expected in generator.STATIC_SITES.items():
            root = standard_deploy.STATIC_ROOTS[domain]
            print(f"Reading recipient route: {domain} (static)", file=sys.stderr, flush=True)
            checks.append(
                file_check(
                    sftp,
                    domain,
                    root / "client-standard-mail.php",
                    expected,
                    "static_standard",
                )
            )

        for domain, expected in CUSTOM_RECIPIENTS.items():
            path = REMOTE_HOME / domain / "public_html/mail.php"
            print(f"Reading recipient route: {domain} (custom)", file=sys.stderr, flush=True)
            checks.append(file_check(sftp, domain, path, expected, "custom_php"))

    for domain, expected in CURRENT_CF7_RECIPIENTS.items():
        definitions = custom_deploy.CF7_FORMS[domain]
        for form_kind in ("callback", "question"):
            print(
                f"Reading recipient route: {domain} (cf7 {form_kind})",
                file=sys.stderr,
                flush=True,
            )
            definition = definitions[form_kind]
            checks.append(
                cf7_check(
                    ssh,
                    {
                        "domain": domain,
                        "root": definitions["root"],
                        "form_id": definition["id"],
                        "title": definition["title"],
                        "expected_recipient": expected,
                    },
                    f"cf7_{form_kind}",
                )
            )

    for contract in legacy_cf7_contracts():
        print(
            f"Reading recipient route: {contract['domain']} (cf7 legacy {contract['form_id']})",
            file=sys.stderr,
            flush=True,
        )
        checks.append(cf7_check(ssh, contract, "cf7_legacy"))
    return checks


def collect_checks_with_retries(
    args,
    *,
    connector=None,
    collector=None,
    attempts: int = 3,
    retry_delay: float = 2.0,
) -> list[dict[str, Any]]:
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    connector = connector or custom_deploy.connect
    collector = collector or collect_checks
    transient_errors = (EOFError, OSError, SSHException)

    for attempt in range(1, attempts + 1):
        ssh = None
        try:
            ssh = connector(args)
            return collector(ssh)
        except transient_errors as error:
            if attempt == attempts:
                raise RuntimeError(
                    f"Recipient matrix could not be read after {attempts} SSH attempts"
                ) from error
            print(
                f"Recipient matrix SSH attempt {attempt}/{attempts} failed: {error}; reconnecting",
                file=sys.stderr,
            )
            if retry_delay:
                time.sleep(retry_delay)
        finally:
            if ssh is not None:
                ssh.close()

    raise RuntimeError("Recipient matrix retry loop ended unexpectedly")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    checks = collect_checks_with_retries(args)

    result = {
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "expected_sites": expected_recipients(),
        "summary": summarize(checks),
        "checks": checks,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 0 if result["summary"]["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
