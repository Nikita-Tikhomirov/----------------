import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.weekly_quality_report import build_quality_report


def test_quality_report_highlights_reopened_task_and_prevention():
    report = build_quality_report(
        {
            "tasks": [
                {
                    "id": "cached-form",
                    "site": "example.ru",
                    "status": "accepted",
                    "financial_classification": "acceptance_fix",
                    "reopened": True,
                    "prevention": {
                        "root_cause": "stale cache",
                        "regression_protection": "clean URL smoke test",
                    },
                }
            ]
        },
        {"messages": [{"id": "mail-1"}]},
        [],
        [],
        as_of=date(2026, 7, 26),
    )

    assert "# Weekly quality review: 2026-07-26" in report
    assert "Processed inbound messages: 1" in report
    assert "cached-form (example.ru): stale cache -> clean URL smoke test" in report


def test_quality_report_calls_out_pending_actions():
    report = build_quality_report(
        {"tasks": []},
        {"messages": []},
        [{"site": "example.ru", "action": "request_mailbox_access", "reason": "delivery check overdue"}],
        [{"site": "blocked.ru", "action": "request_unblock", "reason": "needs DNS data"}],
        as_of=date(2026, 7, 26),
    )

    assert "example.ru: request_mailbox_access - delivery check overdue" in report
    assert "blocked.ru: request_unblock - needs DNS data" in report
