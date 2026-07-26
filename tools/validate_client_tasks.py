"""Validate that client tasks have enough evidence for their status."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


FINAL_STATUSES = {"verifying", "client_review", "accepted"}
VALID_STATUSES = {"new", "in_progress", "blocked", *FINAL_STATUSES}
VALID_FINANCIAL_CLASSES = {
    "main_package",
    "acceptance_fix",
    "warranty_fix",
    "new_work",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nested(record: dict[str, Any], *keys: str) -> Any:
    current: Any = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def validate_register(registry: dict[str, Any], root: Path | None = None) -> list[str]:
    """Return human-readable errors for incomplete task evidence."""
    del root  # Evidence may be on the live server or in Gmail, not only locally.
    errors: list[str] = []
    tasks = registry.get("tasks")

    if not isinstance(tasks, list) or not tasks:
        return ["register: tasks must be a non-empty list"]

    task_ids = [task.get("id") for task in tasks if isinstance(task, dict)]
    duplicate_ids = [task_id for task_id, count in Counter(task_ids).items() if task_id and count > 1]
    if duplicate_ids:
        errors.extend(f"register: duplicate task id {task_id}" for task_id in duplicate_ids)

    for task in tasks:
        if not isinstance(task, dict):
            errors.append("register: task must be an object")
            continue

        task_id = task.get("id")
        if not _nonempty(task_id):
            errors.append("register: task is missing id")
            continue

        status = task.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{task_id}: invalid status {status!r}")

        if task.get("financial_classification") not in VALID_FINANCIAL_CLASSES:
            errors.append(f"{task_id}: invalid financial classification")

        if status not in FINAL_STATUSES:
            continue

        if not _nonempty(_nested(task, "request", "email_message_id")):
            errors.append(f"{task_id}: missing source email message id")
        if not _nonempty(_nested(task, "backup", "location")):
            errors.append(f"{task_id}: missing backup location")
        if not _nonempty(_nested(task, "publication", "live_url")):
            errors.append(f"{task_id}: missing published live URL")

        functional = _nested(task, "verification", "functional")
        if not isinstance(functional, list) or not functional:
            errors.append(f"{task_id}: missing functional verification")
        if not _nonempty(_nested(task, "verification", "visual", "desktop")):
            errors.append(f"{task_id}: missing desktop visual evidence")
        if not _nonempty(_nested(task, "verification", "visual", "mobile")):
            errors.append(f"{task_id}: missing mobile visual evidence")

        if status in {"client_review", "accepted"} and not _nonempty(
            _nested(task, "client_report", "email_message_id")
        ):
            errors.append(f"{task_id}: missing client report message id")

        if status == "accepted":
            acceptance = _nested(task, "client_acceptance")
            has_acceptance = isinstance(acceptance, dict) and any(
                _nonempty(acceptance.get(field)) for field in ("email_message_id", "evidence")
            )
            if not has_acceptance:
                errors.append(f"{task_id}: accepted task is missing client acceptance evidence")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "register",
        nargs="?",
        default="client_tasks.json",
        type=Path,
        help="path to the machine-readable client task register",
    )
    args = parser.parse_args()

    try:
        registry = json.loads(args.register.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read {args.register}: {error}")
        return 2

    errors = validate_register(registry, root=Path.cwd())
    if errors:
        print("Client task quality gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    counts = Counter(task["status"] for task in registry["tasks"])
    summary = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
    print(f"Client task quality gate passed: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
