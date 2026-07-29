"""Gate one daily client report by Moscow calendar date."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

try:
    from tools.email_intake import _write_json_atomically
except ModuleNotFoundError:  # Supports direct execution from tools/.
    from email_intake import _write_json_atomically


MOSCOW = ZoneInfo("Europe/Moscow")


def report_target_date(
    now: datetime,
    *,
    cutoff_hour: int,
    cutoff_minute: int,
) -> date:
    """Return the latest Moscow date whose report should already exist."""
    local_now = now.astimezone(MOSCOW)
    cutoff_reached = (local_now.hour, local_now.minute) >= (
        cutoff_hour,
        cutoff_minute,
    )
    if cutoff_reached:
        return local_now.date()
    return local_now.date() - timedelta(days=1)


def report_due(
    state: dict[str, Any],
    now: datetime,
    *,
    cutoff_hour: int,
    cutoff_minute: int,
) -> bool:
    """Return whether the latest reportable date has not been sent."""
    target_date = report_target_date(
        now,
        cutoff_hour=cutoff_hour,
        cutoff_minute=cutoff_minute,
    )
    return state.get("last_report_date") != target_date.isoformat()


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("daily report state must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state",
        type=Path,
        default=Path(".runtime/client-daily-report-ap-real.json"),
    )
    parser.add_argument("--cutoff-hour", type=int, default=23)
    parser.add_argument("--cutoff-minute", type=int, default=30)
    parser.add_argument("--mark-sent", action="store_true")
    args = parser.parse_args()

    try:
        state = _load_state(args.state)
        now = datetime.now(MOSCOW)
        target_date = report_target_date(
            now,
            cutoff_hour=args.cutoff_hour,
            cutoff_minute=args.cutoff_minute,
        )
        if args.mark_sent:
            state = {
                "last_report_date": target_date.isoformat(),
                "last_report_at": now.isoformat(),
            }
            _write_json_atomically(args.state, state)
        due = report_due(
            state,
            now,
            cutoff_hour=args.cutoff_hour,
            cutoff_minute=args.cutoff_minute,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Daily report gate failed: {error}")
        return 2

    print(
        json.dumps(
            {
                "moscow_date": now.date().isoformat(),
                "report_date": target_date.isoformat(),
                "due": due,
                "last_report_date": state.get("last_report_date"),
                "state_path": str(args.state),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
