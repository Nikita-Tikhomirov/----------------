import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.form_delivery_schedule import build_delivery_queue


def check(**overrides):
    result = {
        "id": "example-form",
        "site": "example.ru",
        "last_verified_at": "2026-07-01",
        "max_age_days": 30,
        "mailbox_access": "available",
    }
    result.update(overrides)
    return result


def test_recent_delivery_check_is_not_queued():
    actions = build_delivery_queue({"checks": [check()]}, today=date(2026, 7, 26))

    assert actions == []


def test_due_check_with_mailbox_access_requests_real_delivery_test():
    actions = build_delivery_queue({"checks": [check()]}, today=date(2026, 8, 1))

    assert actions[0]["action"] == "run_delivery_check"


def test_due_check_without_mailbox_access_requests_access_first():
    actions = build_delivery_queue(
        {"checks": [check(mailbox_access="unavailable")]}, today=date(2026, 8, 1)
    )

    assert actions[0]["action"] == "request_mailbox_access"
