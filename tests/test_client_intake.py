import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.client_intake import intake_message
from tools.client_message_router import ClientProfile


PROFILE = ClientProfile.from_mapping(
    {
        "id": "ap-real",
        "company_names": ["ГК АП-Риал"],
        "contacts": ["upreal@bk.ru"],
        "domains": ["nousro-nn.ru"],
        "financial_keywords": ["счет"],
        "excluded_signals": ["stithc65"],
        "provider_domains": ["beget.ru"],
        "provider_keywords": ["dns"],
    }
)


def test_records_routing_evidence_for_new_sender_with_client_domain():
    ledger, result = intake_message(
        {"messages": []},
        PROFILE,
        {
            "id": "new-email",
            "thread_id": "new-thread",
            "from": "info@nousro.ru",
            "subject": "NOUSRO-NN.RU",
            "body": "Файл с проблемами",
            "received_at": "2026-07-26T12:00:00+03:00",
            "attachments": ["Проблемы с NOUSRO-NN.RU.docx"],
        },
    )

    assert result.bucket == "technical"
    assert result.created is True
    assert ledger["messages"][0]["task_id"] == "triage-ap-real-new-email"
    assert ledger["messages"][0]["routing"]["evidence"] == ["domain:nousro-nn.ru"]


def test_enriches_legacy_deduplicated_message_with_routing_evidence():
    legacy = {
        "messages": [
            {
                "id": "new-email",
                "thread_id": "new-thread",
                "from": "info@nousro.ru",
                "subject": "NOUSRO-NN.RU",
                "received_at": "2026-07-26T12:00:00+03:00",
                "task_id": "old-task",
                "attachments": ["Проблемы с NOUSRO-NN.RU.docx"],
                "state": "processed",
            }
        ]
    }

    ledger, result = intake_message(
        legacy,
        PROFILE,
        {
            "id": "new-email",
            "thread_id": "new-thread",
            "from": "info@nousro.ru",
            "subject": "NOUSRO-NN.RU",
            "body": "Файл с проблемами",
            "received_at": "2026-07-26T12:00:00+03:00",
            "attachments": ["Проблемы с NOUSRO-NN.RU.docx"],
        },
    )

    assert result.created is False
    assert ledger["messages"][0]["routing"]["bucket"] == "technical"


def test_marks_enriched_legacy_message_as_changed_for_persistence():
    legacy = {
        "messages": [
            {
                "id": "new-email",
                "thread_id": "new-thread",
                "from": "info@nousro.ru",
                "subject": "NOUSRO-NN.RU",
                "received_at": "2026-07-26T12:00:00+03:00",
                "task_id": "old-task",
                "attachments": [],
                "state": "processed",
            }
        ]
    }

    _, result = intake_message(
        legacy,
        PROFILE,
        {
            "id": "new-email",
            "thread_id": "new-thread",
            "from": "info@nousro.ru",
            "subject": "NOUSRO-NN.RU",
            "body": "Файл с проблемами",
            "received_at": "2026-07-26T12:00:00+03:00",
            "attachments": [],
        },
    )

    assert result.changed is True


def test_keeps_a_caller_supplied_existing_task_id_when_importing_history():
    ledger, _ = intake_message(
        {"messages": []},
        PROFILE,
        {
            "id": "accepted-email",
            "thread_id": "accepted-thread",
            "from": "info@nousro.ru",
            "subject": "NOUSRO-NN.RU",
            "body": "Файл с проблемами",
            "received_at": "2026-07-26T12:00:00+03:00",
            "attachments": [],
        },
        task_id="form-acceptance-20260724",
    )

    assert ledger["messages"][0]["task_id"] == "form-acceptance-20260724"
