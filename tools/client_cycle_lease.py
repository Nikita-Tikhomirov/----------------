"""Prevent overlapping autonomous client-cycle runs."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from tools.email_intake import _write_json_atomically
except ModuleNotFoundError:  # Supports direct execution from tools/.
    from email_intake import _write_json_atomically


def _expires_at(now: datetime, ttl_minutes: int) -> str:
    return (now + timedelta(minutes=ttl_minutes)).isoformat()


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("lease timestamp must include a timezone")
    return parsed


def acquire_lease(
    state: dict[str, Any],
    run_id: str,
    now: datetime,
    *,
    ttl_minutes: int,
) -> tuple[dict[str, Any], bool, bool]:
    """Acquire an empty or expired lease without replacing an active owner."""
    active_run_id = state.get("run_id")
    expires_at = _parse_timestamp(state.get("expires_at"))
    if active_run_id and expires_at and expires_at > now:
        return state, False, False

    recovered = bool(active_run_id)
    return (
        {
            "run_id": run_id,
            "started_at": now.isoformat(),
            "renewed_at": now.isoformat(),
            "expires_at": _expires_at(now, ttl_minutes),
        },
        True,
        recovered,
    )


def renew_lease(
    state: dict[str, Any],
    run_id: str,
    now: datetime,
    *,
    ttl_minutes: int,
) -> tuple[dict[str, Any], bool]:
    """Extend a lease only for its current owner."""
    if state.get("run_id") != run_id:
        return state, False
    renewed = dict(state)
    renewed["renewed_at"] = now.isoformat()
    renewed["expires_at"] = _expires_at(now, ttl_minutes)
    return renewed, True


def release_lease(
    state: dict[str, Any], run_id: str
) -> tuple[dict[str, Any], bool]:
    """Release a lease only for its current owner."""
    if state.get("run_id") != run_id:
        return state, False
    return {}, True


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("cycle lease state must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state",
        type=Path,
        default=Path(".runtime/client-cycle-ap-real-lease.json"),
    )
    parser.add_argument("--ttl-minutes", type=int, default=90)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--acquire", action="store_true")
    action.add_argument("--renew")
    action.add_argument("--release")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    if args.ttl_minutes < 1:
        parser.error("--ttl-minutes must be positive")

    try:
        state = _load_state(args.state)
        now = datetime.now(timezone.utc)
        if args.acquire:
            run_id = args.run_id or uuid.uuid4().hex
            updated, ok, recovered = acquire_lease(
                state, run_id, now, ttl_minutes=args.ttl_minutes
            )
            if ok:
                _write_json_atomically(args.state, updated)
            result = {
                "action": "acquire",
                "ok": ok,
                "run_id": run_id if ok else state.get("run_id"),
                "expires_at": updated.get("expires_at"),
                "recovered_stale_lease": recovered,
            }
        elif args.renew:
            updated, ok = renew_lease(
                state, args.renew, now, ttl_minutes=args.ttl_minutes
            )
            if ok:
                _write_json_atomically(args.state, updated)
            result = {
                "action": "renew",
                "ok": ok,
                "run_id": args.renew,
                "expires_at": updated.get("expires_at"),
            }
        else:
            updated, ok = release_lease(state, args.release)
            if ok:
                _write_json_atomically(args.state, updated)
            result = {"action": "release", "ok": ok, "run_id": args.release}
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Client cycle lease failed: {error}")
        return 2

    print(json.dumps(result, ensure_ascii=False))
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
