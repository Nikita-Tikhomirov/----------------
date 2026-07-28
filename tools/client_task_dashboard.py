"""Build a deterministic action queue from the client task register."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


FOLLOW_UP_AFTER_BUSINESS_DAYS = 3


def _business_days_since(start: date, end: date) -> int:
    return sum(
        current.weekday() < 5
        for current in (start.fromordinal(day) for day in range(start.toordinal() + 1, end.toordinal() + 1))
    )


def _action(task: dict[str, Any], action: str, reason: str) -> dict[str, str]:
    return {
        "task_id": task["id"],
        "site": task.get("site", "unknown site"),
        "action": action,
        "reason": reason,
    }


def _report_date(task: dict[str, Any]) -> date | None:
    client_report = task.get("client_report")
    if not isinstance(client_report, dict):
        return None

    sent_at = client_report.get("sent_at")
    if not isinstance(sent_at, str) or not sent_at.strip():
        return None

    try:
        return datetime.fromisoformat(sent_at).date()
    except ValueError:
        return None


def _scheduled_action_date(task: dict[str, Any]) -> date | None:
    value = task.get("next_action_at")
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def build_action_queue(registry: dict[str, Any], today: date | None = None) -> list[dict[str, str]]:
    """Return the next required action for every non-final task."""
    today = today or date.today()
    actions: list[dict[str, str]] = []

    for task in registry.get("tasks", []):
        if not isinstance(task, dict) or not isinstance(task.get("id"), str):
            continue

        status = task.get("status")
        if status == "new":
            actions.append(
                _action(task, "triage", "new client request needs full reading and task breakdown")
            )
        elif status == "in_progress":
            actions.append(_action(task, "continue_work", "implementation and QA are not complete"))
        elif status == "blocked":
            scheduled_for = _scheduled_action_date(task)
            if scheduled_for is None or today >= scheduled_for:
                actions.append(_action(task, "request_unblock", "client or provider data is required"))
        elif status == "client_review":
            report_date = _report_date(task)
            if report_date is None:
                actions.append(
                    _action(task, "record_report_timestamp", "client report timestamp is required for follow-up")
                )
            elif (
                (_scheduled_action_date(task) is None or today >= _scheduled_action_date(task))
                and _business_days_since(report_date, today) >= FOLLOW_UP_AFTER_BUSINESS_DAYS
            ):
                actions.append(
                    _action(
                        task,
                        "follow_up_client_review",
                        "client review has exceeded three business days",
                    )
                )

    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("register", nargs="?", default="client_tasks.json", type=Path)
    parser.add_argument("--json", action="store_true", help="print a machine-readable queue")
    args = parser.parse_args()

    try:
        registry = json.loads(args.register.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read {args.register}: {error}")
        return 2

    actions = build_action_queue(registry)
    if args.json:
        print(json.dumps(actions, ensure_ascii=False, indent=2))
    elif actions:
        print("Client task action queue:")
        for action in actions:
            print(f"- [{action['action']}] {action['site']}: {action['reason']}")
    else:
        print("Client task action queue is empty.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
