"""Persist processed client email metadata to prevent duplicate task intake."""

from __future__ import annotations

import argparse
import copy
import json
import os
import tempfile
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = ("id", "thread_id", "from", "subject", "received_at", "task_id")


def register_message(ledger: dict[str, Any], message: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return an updated ledger and whether the message was newly recorded."""
    missing = [field for field in REQUIRED_FIELDS if not isinstance(message.get(field), str) or not message[field].strip()]
    if missing:
        raise ValueError(f"message is missing required fields: {', '.join(missing)}")

    updated = copy.deepcopy(ledger)
    messages = updated.setdefault("messages", [])
    if not isinstance(messages, list):
        raise ValueError("ledger messages must be a list")
    if any(existing.get("id") == message["id"] for existing in messages if isinstance(existing, dict)):
        return updated, False

    recorded = {**message, "attachments": list(message.get("attachments", [])), "state": "processed"}
    messages.append(recorded)
    return updated, True


def _write_json_atomically(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp"
    ) as temporary_file:
        json.dump(value, temporary_file, ensure_ascii=False, indent=2)
        temporary_file.write("\n")
        temporary_path = Path(temporary_file.name)
    os.replace(temporary_path, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=Path("email_intake.json"))
    parser.add_argument("--message-id", required=True)
    parser.add_argument("--thread-id", required=True)
    parser.add_argument("--from", dest="sender", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--received-at", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--attachment", action="append", default=[])
    args = parser.parse_args()

    try:
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        updated, created = register_message(
            ledger,
            {
                "id": args.message_id,
                "thread_id": args.thread_id,
                "from": args.sender,
                "subject": args.subject,
                "received_at": args.received_at,
                "task_id": args.task_id,
                "attachments": args.attachment,
            },
        )
        if created:
            _write_json_atomically(args.ledger, updated)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Email intake failed: {error}")
        return 2

    print(json.dumps({"message_id": args.message_id, "created": created}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
