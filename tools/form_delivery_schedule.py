"""Queue periodic real form-delivery tests without sending unsolicited traffic."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


def build_delivery_queue(config: dict[str, Any], today: date | None = None) -> list[dict[str, str]]:
    """Return due delivery checks and the safe next action for each one."""
    today = today or date.today()
    actions: list[dict[str, str]] = []
    for check in config.get("checks", []):
        verified_at = date.fromisoformat(check["last_verified_at"])
        if (today - verified_at).days < check["max_age_days"]:
            continue

        has_access = check.get("mailbox_access") == "available"
        action = "run_delivery_check" if has_access else "request_mailbox_access"
        actions.append(
            {
                "check_id": check["id"],
                "site": check["site"],
                "action": action,
                "reason": f"delivery verification is older than {check['max_age_days']} days",
            }
        )
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("form_delivery_checks.json"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        actions = build_delivery_queue(config)
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"Form delivery schedule error: {error}")
        return 2

    if args.json:
        print(json.dumps(actions, ensure_ascii=False, indent=2))
    elif actions:
        print("Form delivery schedule:")
        for action in actions:
            print(f"- [{action['action']}] {action['site']}: {action['reason']}")
    else:
        print("Form delivery schedule is empty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
