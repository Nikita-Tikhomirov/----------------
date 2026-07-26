import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.client_task_dashboard import build_action_queue
from tools.validate_client_tasks import validate_register


def task(status, **extra):
    result = {
        "id": "task-1",
        "site": "example.ru",
        "status": status,
        "financial_classification": "acceptance_fix",
    }
    result.update(extra)
    return result


def test_new_task_is_added_to_triage_queue():
    actions = build_action_queue({"tasks": [task("new")]}, today=date(2026, 7, 26))

    assert actions == [
        {
            "task_id": "task-1",
            "site": "example.ru",
            "action": "triage",
            "reason": "new client request needs full reading and task breakdown",
        }
    ]


def test_client_review_without_report_timestamp_is_data_integrity_action():
    actions = build_action_queue(
        {"tasks": [task("client_review", client_report={"email_message_id": "abc12345"})]},
        today=date(2026, 7, 26),
    )

    assert actions[0]["action"] == "record_report_timestamp"


def test_client_review_is_followed_up_after_three_business_days():
    actions = build_action_queue(
        {
            "tasks": [
                task(
                    "client_review",
                    client_report={
                        "email_message_id": "abc12345",
                        "sent_at": "2026-07-20T12:00:00+03:00",
                    },
                )
            ]
        },
        today=date(2026, 7, 23),
    )

    assert actions[0]["action"] == "follow_up_client_review"


def test_blocked_task_waits_until_its_scheduled_follow_up_date():
    registry = {
        "tasks": [task("blocked", next_action_at="2026-07-29")],
    }

    assert build_action_queue(registry, today=date(2026, 7, 26)) == []
    assert build_action_queue(registry, today=date(2026, 7, 29))[0]["action"] == "request_unblock"


def test_reopened_task_requires_root_cause_and_regression_protection():
    errors = validate_register(
        {
            "tasks": [
                task(
                    "in_progress",
                    reopened=True,
                    request={"email_message_id": "abc12345"},
                )
            ]
        }
    )

    assert "task-1: reopened task is missing prevention root cause" in errors
    assert "task-1: reopened task is missing regression protection" in errors
