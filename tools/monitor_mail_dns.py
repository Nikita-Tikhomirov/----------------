"""Monitor critical MX, SPF and DKIM DNS records through DNS-over-HTTPS."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DNS_ENDPOINT = "https://dns.google/resolve"
USER_AGENT = "APRealMailDnsMonitor/1.0 (+https://www.apreal.ru/)"


def _normalize_txt(record: str) -> str:
    return record.replace('"', "").strip()


def _mx_target(record: str) -> str:
    return record.split()[-1].rstrip(".").lower()


def evaluate_dns_target(target: dict[str, Any], records: dict[str, list[str]]) -> dict[str, Any]:
    """Compare resolved mail DNS records with the approved expected values."""
    issues: list[str] = []
    mx_targets = {_mx_target(record) for record in records.get("mx", []) if record.split()}
    for expected in target.get("expected_mx", []):
        if expected.lower() not in mx_targets:
            issues.append(f"missing MX target: {expected}")

    spf_text = " ".join(_normalize_txt(record) for record in records.get("spf", []))
    for marker in target.get("spf_required", []):
        if marker.lower() not in spf_text.lower():
            issues.append(f"SPF is missing required marker: {marker}")

    dkim_text = " ".join(_normalize_txt(record) for record in records.get("dkim", []))
    for marker in target.get("dkim", {}).get("required", []):
        if marker.lower() not in dkim_text.lower():
            issues.append(f"DKIM is missing required marker: {marker}")

    return {
        "target_id": target["id"],
        "domain": target["domain"],
        "healthy": not issues,
        "issues": issues,
        "records": records,
    }


def _query_records(name: str, record_type: str, timeout_seconds: float) -> list[str]:
    query = urlencode({"name": name, "type": record_type})
    request = Request(f"{DNS_ENDPOINT}?{query}", headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("Status") != 0:
        return []
    return [answer["data"] for answer in payload.get("Answer", []) if "data" in answer]


def fetch_dns_records(target: dict[str, Any], timeout_seconds: float) -> dict[str, list[str]]:
    domain_txt = _query_records(target["domain"], "TXT", timeout_seconds)
    dkim_name = target.get("dkim", {}).get("name")
    return {
        "mx": _query_records(target["domain"], "MX", timeout_seconds),
        "spf": [record for record in domain_txt if _normalize_txt(record).lower().startswith("v=spf1")],
        "dkim": _query_records(dkim_name, "TXT", timeout_seconds) if dkim_name else [],
    }


def load_targets(config_path: Path) -> list[dict[str, Any]]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    targets = config.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ValueError("mail DNS config must contain a non-empty targets list")
    return targets


def run_monitor(config_path: Path, timeout_seconds: float) -> dict[str, Any]:
    results = []
    for target in load_targets(config_path):
        try:
            results.append(evaluate_dns_target(target, fetch_dns_records(target, timeout_seconds)))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            results.append(
                {
                    "target_id": target.get("id", "unknown"),
                    "domain": target.get("domain", "unknown"),
                    "healthy": False,
                    "issues": [f"DNS query error: {error}"],
                    "records": {},
                }
            )
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "healthy": all(result["healthy"] for result in results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("mail_dns_targets.json"))
    parser.add_argument("--output", type=Path, default=Path("output/monitoring/mail-dns.json"))
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    try:
        report = run_monitor(args.config, args.timeout)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Mail DNS monitor configuration error: {error}")
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unhealthy = [result for result in report["results"] if not result["healthy"]]
    print(f"Mail DNS monitor: {len(report['results']) - len(unhealthy)}/{len(report['results'])} healthy")
    for result in unhealthy:
        print(f"- {result['target_id']}: {'; '.join(result['issues'])}")
    return 1 if unhealthy and args.fail_on_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
