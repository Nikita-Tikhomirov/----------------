#!/usr/bin/env python3
"""Run each domain QA in a fresh process so one legacy site cannot stall all."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


BASE = Path(__file__).resolve().parent
SCOPE = json.loads((BASE / "form-audit-scope.json").read_text(encoding="utf-8"))
QA_SCRIPT = BASE / "qa_forms.py"
OUTPUT = BASE / "browser-qa-results.json"
WORK = Path(tempfile.gettempdir()) / "beget-form-qa-isolated"


def run_domain(domain: str) -> dict:
    result_file = WORK / f"{domain}.json"
    command = [
        sys.executable,
        str(QA_SCRIPT),
        "--domain",
        domain,
        "--output",
        str(result_file),
    ]
    last_error = ""
    for attempt in range(1, 4):
        result_file.unlink(missing_ok=True)
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            last_error = (
                f"Attempt {attempt}: isolated browser QA timed out "
                "after 60 seconds"
            )
            continue

        if not result_file.is_file():
            last_error = (
                f"Attempt {attempt}: QA exited {completed.returncode} "
                f"without a result: {completed.stderr[-500:]}"
            )
            continue
        payload = json.loads(result_file.read_text(encoding="utf-8"))
        result = payload["results"][0]
        if completed.returncode not in (0, 1) and not result.get("error"):
            result["error"] = (
                f"QA process exited {completed.returncode}: "
                f"{completed.stderr[-500:]}"
            )
        if result.get("error") and attempt < 3:
            last_error = f"Attempt {attempt}: {result['error']}"
            continue
        return result

    return {
        "domain": domain,
        "status": 0,
        "meaningful_body": False,
        "standard_component": False,
        "error": last_error,
    }


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    results = []
    for index, site in enumerate(SCOPE["sites"], start=1):
        domain = site["domain"]
        result = run_domain(domain)
        results.append(result)
        print(
            f"{index}/{len(SCOPE['sites'])} {domain} "
            f"{'ERROR' if result.get('error') else 'OK'}",
            flush=True,
        )

    OUTPUT.write_text(
        json.dumps(
            {
                "screenshot_dir": str(
                    Path(tempfile.gettempdir()) / "beget-form-qa-2026-07-20"
                ),
                "execution": "isolated-per-domain",
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    failed = [
        item
        for item in results
        if item.get("error")
        or item.get("status") != 200
        or not item.get("meaningful_body")
        or (
            item.get("standard_component")
            and (
                not item.get("mobile", {}).get("modal_visible")
                or not item.get("mobile", {}).get("fits_viewport")
            )
        )
    ]
    print(
        json.dumps(
            {
                "total": len(results),
                "failed": [item["domain"] for item in failed],
            },
            ensure_ascii=True,
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
