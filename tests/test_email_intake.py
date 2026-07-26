import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.email_intake import register_message


MESSAGE = {
    "id": "message-123",
    "thread_id": "thread-456",
    "from": "client@example.ru",
    "subject": "Site issue",
    "received_at": "2026-07-26T12:00:00+03:00",
    "task_id": "example-task",
    "attachments": ["screenshot.png"],
}


def test_new_message_is_recorded_as_processed():
    ledger, created = register_message({"messages": []}, MESSAGE)

    assert created is True
    assert ledger["messages"] == [{**MESSAGE, "state": "processed"}]


def test_duplicate_message_is_not_added_twice():
    existing = {"messages": [{**MESSAGE, "state": "processed"}]}

    ledger, created = register_message(existing, MESSAGE)

    assert created is False
    assert len(ledger["messages"]) == 1
