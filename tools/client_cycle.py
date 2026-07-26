"""Print the deterministic Gmail search plan for one client profile."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
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


@dataclass(frozen=True)
class ScanState:
    """Timestamp of the last Gmail scan that reached its known-message boundary."""

    last_success_at: str


@dataclass(frozen=True)
class CyclePlan:
    """Bounded Gmail search contract for one client cycle."""

    mode: str
    queries: tuple[str, ...]
    max_pages: int
    stop_when_page_is_fully_known: bool = True


def load_scan_state(path: Path) -> ScanState | None:
    """Load a successful scan marker without treating a missing marker as an error."""
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    timestamp = value.get("last_success_at") if isinstance(value, dict) else None
    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("scan state last_success_at must be a non-empty string")
    return ScanState(last_success_at=timestamp)


def build_cycle_plan(profile: ClientProfile, state: ScanState | None) -> CyclePlan:
    """Use the full lookback only until a complete scan has succeeded once."""
    if state is None:
        return CyclePlan(
            mode="bootstrap",
            queries=build_search_queries(profile),
            max_pages=10,
        )
    return CyclePlan(
        mode="incremental",
        queries=build_search_queries(profile, lookback_days=profile.mail_incremental_lookback_days),
        max_pages=3,
    )


def default_state_path(profile: ClientProfile) -> Path:
    return Path(".runtime") / f"client-cycle-{profile.id}.json"


def mark_scan_success(path: Path) -> ScanState:
    """Persist a marker only after Gmail pagination completed without connector errors."""
    state = ScanState(last_success_at=datetime.now(timezone.utc).isoformat())
    _write_json_atomically(path, {"last_success_at": state.last_success_at})
    return state


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
    parser.add_argument("--state", type=Path)
    parser.add_argument("--mark-success", action="store_true")
    args = parser.parse_args()

    try:
        profile = ClientProfile.from_json_file(args.profile)
        ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
        ledger, changed = separate_ignored_messages(ledger)
        if changed:
            _write_json_atomically(args.ledger, ledger)
        seen_ids = known_message_ids(ledger)
        state_path = args.state or default_state_path(profile)
        if args.mark_success:
            state = mark_scan_success(state_path)
            print(json.dumps({"profile_id": profile.id, "scan_state": state.__dict__}, ensure_ascii=False))
            return 0
        state = load_scan_state(state_path)
        plan = build_cycle_plan(profile, state)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Client cycle failed: {error}")
        return 2

    print(
        json.dumps(
            {
                "profile_id": profile.id,
                "gmail_queries": plan.queries,
                "seen_message_ids": sorted(seen_ids),
                "scan_contract": {
                    "mode": plan.mode,
                    "max_pages": plan.max_pages,
                    "stop_when_page_is_fully_known": plan.stop_when_page_is_fully_known,
                    "mark_success_command": "run this command with --mark-success only after every Gmail query completes without errors",
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
