"""Safely monitor public client pages without sending form submissions."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = "APRealSiteMonitor/1.0 (+https://www.apreal.ru/)"


def evaluate_response(
    target: dict[str, Any], status_code: int, body: str, elapsed_ms: int
) -> dict[str, Any]:
    """Turn one HTTP response into a portable health-check result."""
    expected_statuses = target.get("expected_statuses", [200])
    issues: list[str] = []
    if status_code not in expected_statuses:
        issues.append(f"unexpected HTTP status {status_code}")

    body_lower = body.lower()
    for marker in target.get("error_patterns", []):
        if marker.lower() in body_lower:
            issues.append(f"page contains error marker: {marker}")

    for marker in target.get("required_markers", []):
        if marker.lower() not in body_lower:
            issues.append(f"page is missing required marker: {marker}")

    return {
        "target_id": target["id"],
        "url": target["url"],
        "status_code": status_code,
        "elapsed_ms": elapsed_ms,
        "healthy": not issues,
        "issues": issues,
    }


def check_target(target: dict[str, Any], timeout_seconds: float) -> dict[str, Any]:
    """Fetch a target and convert HTTP or network failures to a health result."""
    request = Request(target["url"], headers={"User-Agent": USER_AGENT})
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = response.status
            body = response.read().decode("utf-8", errors="replace")
    except HTTPError as error:
        status_code = error.code
        body = error.read().decode("utf-8", errors="replace")
    except (OSError, URLError) as error:
        return {
            "target_id": target["id"],
            "url": target["url"],
            "status_code": None,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "healthy": False,
            "issues": [f"network error: {error.reason if isinstance(error, URLError) else error}"],
        }

    return evaluate_response(
        target,
        status_code,
        body,
        int((time.monotonic() - started) * 1000),
    )


def load_targets(config_path: Path) -> list[dict[str, Any]]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    defaults = config.get("defaults", {})
    targets = config.get("targets", [])
    if not isinstance(targets, list) or not targets:
        raise ValueError("monitoring config must contain a non-empty targets list")

    resolved_targets = []
    target_ids: set[str] = set()
    target_urls: set[str] = set()
    for target in targets:
        if not isinstance(target, dict) or not target.get("id") or not target.get("url"):
            raise ValueError("each monitoring target needs id and url")
        if target["id"] in target_ids:
            raise ValueError(f"duplicate monitoring target id: {target['id']}")
        if target["url"] in target_urls:
            raise ValueError(f"duplicate monitoring target URL: {target['url']}")
        target_ids.add(target["id"])
        target_urls.add(target["url"])
        resolved_targets.append({**defaults, **target})
    return resolved_targets


def run_monitor(config_path: Path, timeout_seconds: float) -> dict[str, Any]:
    targets = load_targets(config_path)
    with ThreadPoolExecutor(max_workers=min(6, len(targets))) as executor:
        results = list(executor.map(lambda target: check_target(target, timeout_seconds), targets))
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "healthy": all(result["healthy"] for result in results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("monitoring_targets.json"))
    parser.add_argument("--output", type=Path, default=Path("output/monitoring/latest.json"))
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    try:
        report = run_monitor(args.config, args.timeout)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Site monitor configuration error: {error}")
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    unhealthy = [result for result in report["results"] if not result["healthy"]]
    print(f"Site monitor: {len(report['results']) - len(unhealthy)}/{len(report['results'])} healthy")
    for result in unhealthy:
        print(f"- {result['target_id']}: {'; '.join(result['issues'])}")
    return 1 if unhealthy and args.fail_on_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
