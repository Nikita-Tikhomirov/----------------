from datetime import datetime
from zoneinfo import ZoneInfo

from tools.daily_client_report import report_due


MOSCOW = ZoneInfo("Europe/Moscow")


def test_report_is_due_once_after_cutoff():
    now = datetime(2026, 7, 29, 23, 40, tzinfo=MOSCOW)

    assert report_due({}, now, cutoff_hour=23, cutoff_minute=30) is True
    assert (
        report_due(
            {"last_report_date": "2026-07-29"},
            now,
            cutoff_hour=23,
            cutoff_minute=30,
        )
        is False
    )


def test_report_is_not_due_before_cutoff():
    now = datetime(2026, 7, 29, 22, 59, tzinfo=MOSCOW)

    assert report_due({}, now, cutoff_hour=23, cutoff_minute=30) is False
