"""Print the deterministic Gmail search plan for one client profile."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from tools.client_message_router import ClientProfile, build_search_queries
    from tools.client_intake import separate_ignored_messages
    from tools.email_intake import _write_json_atomically
except ModuleNotFoundError:  # Supports ``python tools/client_cycle.py`` in cron.
    from client_message_router import ClientProfile, build_search_queries
    from client_intake import separate_ignored_messages
    from email_intake import _write_json_atomically


def known_message_ids(ledger: dict[str, Any]) -> set[str]:
    """Return already-routed Gmail IDs so a cron run reads only new messages."""
    messages = ledger.get("messages", [])
    ignored = ledger.get("ignored_messages", [])
    if not isinstance(messages, list) or not isinstance(ignored, list):
        raise ValueError("ledger messages and ignored_messages must be lists")
    return {
        message["id"]
        for message in (*messages, *ignored)
        if isinstance(message, dict) and isinstance(message.get("id"), str) and message["id"].strip()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--ledger", default=Path("email_intake.json"), type=Path)
    args = parser.parse_args()

    try:
        profile = ClientProfile.from_json_file(args.profile)
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        ledger, changed = separate_ignored_messages(ledger)
        if changed:
            _write_json_atomically(args.ledger, ledger)
        seen_ids = known_message_ids(ledger)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Client cycle failed: {error}")
        return 2

    print(
        json.dumps(
            {
                "profile_id": profile.id,
                "gmail_queries": build_search_queries(profile),
                "seen_message_ids": sorted(seen_ids),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
