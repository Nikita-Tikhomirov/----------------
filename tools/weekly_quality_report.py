"""Create a concise weekly review of task quality and operational follow-ups."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

try:
    from tools.client_task_dashboard import build_action_queue
    from tools.form_delivery_schedule import build_delivery_queue
    from tools.validate_client_tasks import validate_register
except ModuleNotFoundError:  # Direct execution: python tools/weekly_quality_report.py
    from client_task_dashboard import build_action_queue
    from form_delivery_schedule import build_delivery_queue
    from validate_client_tasks import validate_register


def _format_actions(actions: list[dict[str, str]]) -> list[str]:
    return [f"- {action['site']}: {action['action']} - {action['reason']}" for action in actions]


def build_quality_report(
    task_registry: dict[str, Any],
    email_ledger: dict[str, Any],
    delivery_actions: list[dict[str, str]],
    task_actions: list[dict[str, str]],
    *,
    as_of: date,
) -> str:
    """Render operational evidence into a human-readable weekly report."""
    tasks = task_registry.get("tasks", [])
    status_counts = Counter(task.get("status", "unknown") for task in tasks if isinstance(task, dict))
    lines = [
        f"# Weekly quality review: {as_of.isoformat()}",
        "",
        "## Snapshot",
        f"- Tasks tracked: {len(tasks)}",
        "- Task statuses: " + ", ".join(f"{status}={count}" for status, count in sorted(status_counts.items())),
        f"- Processed inbound messages: {len(email_ledger.get('messages', []))}",
        "",
        "## Returned Work And Prevention",
    ]

    reopened = [task for task in tasks if isinstance(task, dict) and task.get("reopened")]
    if reopened:
        for task in reopened:
            prevention = task.get("prevention", {})
            lines.append(
                f"- {task['id']} ({task.get('site', 'unknown site')}): "
                f"{prevention.get('root_cause', 'root cause missing')} -> "
                f"{prevention.get('regression_protection', 'regression protection missing')}"
            )
    else:
        lines.append("- No returned tasks recorded.")

    lines.extend(["", "## Pending Actions"])
    pending = delivery_actions + task_actions
    lines.extend(_format_actions(pending) if pending else ["- No pending actions."])

    quality_errors = validate_register(task_registry)
    lines.extend(["", "## Quality Gate"])
    lines.extend([f"- {error}" for error in quality_errors] if quality_errors else ["- All tracked tasks pass the quality gate."])
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, default=Path("client_tasks.json"))
    parser.add_argument("--mail", type=Path, default=Path("email_intake.json"))
    parser.add_argument("--delivery", type=Path, default=Path("form_delivery_checks.json"))
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        tasks = _read_json(args.tasks)
        mail = _read_json(args.mail)
        delivery = _read_json(args.delivery)
        report = build_quality_report(
            tasks,
            mail,
            build_delivery_queue(delivery, today=args.date),
            build_action_queue(tasks, today=args.date),
            as_of=args.date,
        )
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"Weekly quality review failed: {error}")
        return 2

    output = args.output or Path("output/quality") / f"weekly-{args.date.isoformat()}.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
