"""Route and persist one Gmail message for a configured client."""

from __future__ import annotations

import argparse
import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from tools.client_message_router import ClientProfile, RoutingDecision, classify_message
    from tools.email_intake import _write_json_atomically, register_message
except ModuleNotFoundError:  # Supports ``python tools/client_intake.py`` in cron.
    from client_message_router import ClientProfile, RoutingDecision, classify_message
    from email_intake import _write_json_atomically, register_message


@dataclass(frozen=True)
class IntakeResult:
    bucket: str
    evidence: tuple[str, ...]
    requires_technical_task: bool
    created: bool
    changed: bool


def _task_id(profile: ClientProfile, message: dict[str, Any], decision: RoutingDecision) -> str:
    prefix = "triage" if decision.requires_technical_task else decision.bucket
    return f"{prefix}-{profile.id}-{message['id']}"


def intake_message(
    ledger: dict[str, Any],
    profile: ClientProfile,
    message: dict[str, Any],
    task_id: str | None = None,
) -> tuple[dict[str, Any], IntakeResult]:
    """Classify and save a message once, preserving the route evidence."""
    decision = classify_message(profile, message)
    record = {
        "id": message["id"],
        "thread_id": message["thread_id"],
        "from": message["from"],
        "subject": message["subject"],
        "received_at": message["received_at"],
        "task_id": task_id or _task_id(profile, message, decision),
        "attachments": list(message.get("attachments", [])),
        "routing": {
            "profile_id": profile.id,
            "bucket": decision.bucket,
            "evidence": list(decision.evidence),
            "requires_technical_task": decision.requires_technical_task,
        },
    }
    updated, created = register_message(ledger, record)
    changed = created
    if not created:
        updated = copy.deepcopy(updated)
        for existing in updated["messages"]:
            if existing.get("id") == message["id"]:
                if "routing" not in existing:
                    existing["routing"] = record["routing"]
                    changed = True
                break
    return updated, IntakeResult(
        bucket=decision.bucket,
        evidence=decision.evidence,
        requires_technical_task=decision.requires_technical_task,
        created=created,
        changed=changed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--ledger", default=Path("email_intake.json"), type=Path)
    parser.add_argument("--message", type=Path)
    parser.add_argument("--message-id")
    parser.add_argument("--thread-id")
    parser.add_argument("--from", dest="sender")
    parser.add_argument("--subject")
    parser.add_argument("--received-at")
    parser.add_argument("--body", default="")
    parser.add_argument("--attachment", action="append", default=[])
    parser.add_argument("--task-id", help="existing task id when importing a known thread")
    args = parser.parse_args()

    try:
        profile = ClientProfile.from_json_file(args.profile)
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        if args.message:
            message = json.loads(args.message.read_text(encoding="utf-8"))
        else:
            scalar_fields = {
                "id": args.message_id,
                "thread_id": args.thread_id,
                "from": args.sender,
                "subject": args.subject,
                "received_at": args.received_at,
            }
            missing = [name for name, value in scalar_fields.items() if not value]
            if missing:
                raise ValueError(
                    "provide --message or scalar fields: " + ", ".join(missing)
                )
            message = {**scalar_fields, "body": args.body, "attachments": args.attachment}
        if not isinstance(message, dict):
            raise ValueError("message must be a JSON object")
        updated, result = intake_message(ledger, profile, message, task_id=args.task_id)
        if result.changed:
            _write_json_atomically(args.ledger, updated)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Client intake failed: {error}")
        return 2

    print(json.dumps(result.__dict__, ensure_ascii=False, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
