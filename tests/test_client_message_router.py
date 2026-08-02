import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.client_cycle import (
    ScanState,
    build_cycle_plan,
    can_mark_scan_success,
    known_message_ids,
    record_unreadable_message,
    resolve_unreadable_message,
)
from tools.client_message_router import ClientProfile, build_search_queries, classify_message


PROFILE = ClientProfile.from_mapping(
    {
        "id": "ap-real",
        "company_names": ["ГК АП-Риал", "Учебный центр"],
        "contacts": ["upreal@bk.ru", "khorov69@mail.ru"],
        "domains": ["apreal.ru", "nousro-nn.ru"],
        "financial_keywords": ["счет", "счёт", "оплата", "бухгалтерия"],
        "excluded_signals": ["stithc65", "Buoyant Tamara"],
        "provider_domains": ["beget.ru"],
        "provider_keywords": ["перенос", "dns", "почт"],
    }
)


def test_routes_new_sender_by_client_domain_in_subject_and_attachment():
    decision = classify_message(
        PROFILE,
        {
            "from": "info@nousro.ru",
            "subject": "NOUSRO-NN.RU",
            "body": "Файл с проблемами прилагаю",
            "attachments": ["Проблемы с NOUSRO-NN.RU.docx"],
        },
    )

    assert decision.bucket == "technical"
    assert "domain:nousro-nn.ru" in decision.evidence


def test_routes_accounting_message_as_finance_without_technical_task():
    decision = classify_message(
        PROFILE,
        {
            "from": "accounting@example.org",
            "subject": "Оплата счета",
            "body": "Бухгалтерия ГК АП-Риал подтверждает оплату",
            "attachments": [],
        },
    )

    assert decision.bucket == "finance"
    assert decision.requires_technical_task is False


def test_technical_request_is_not_lost_when_it_also_mentions_an_invoice():
    decision = classify_message(
        PROFILE,
        {
            "from": "info@nousro.ru",
            "subject": "Сайты и счет",
            "body": "Во вложении проблемы с формами заявок на сайтах ГК АП-Риал.",
            "attachments": [
                "Сайты в т.ч. с битыми заявками.docx",
                "Проблемы с сайтами на 18.07.2026.docx",
            ],
        },
    )

    assert decision.bucket == "technical"
    assert decision.requires_technical_task is True
    assert "technical:проблем" in decision.evidence
    assert "financial:счет" in decision.evidence


def test_does_not_route_unrelated_finance_notice_into_client_finances():
    decision = classify_message(
        PROFILE,
        {
            "from": "support@link-host.net",
            "subject": "Неоплаченный счет",
            "body": "Напоминание об оплате услуг личного аккаунта stitch",
            "attachments": [],
        },
    )

    assert decision.bucket == "unrelated"


def test_excludes_personal_beget_vps_message():
    decision = classify_message(
        PROFILE,
        {
            "from": "support@beget.ru",
            "subject": "Напоминание, аккаунт stithc65",
            "body": "Виртуальный сервер Buoyant Tamara будет заблокирован",
            "attachments": [],
        },
    )

    assert decision.bucket == "unrelated"


def test_requires_client_context_for_provider_message():
    decision = classify_message(
        PROFILE,
        {
            "from": "support@beget.ru",
            "subject": "Перенос DNS для apreal.ru",
            "body": "Настройки почты перенесены",
            "attachments": [],
        },
    )

    assert decision.bucket == "provider"
    assert decision.requires_technical_task is True


def test_search_plan_covers_unread_mail_and_client_context_not_only_known_senders():
    queries = build_search_queries(PROFILE)

    assert "is:unread in:inbox newer_than:30d" in queries
    assert any("nousro-nn.ru" in query for query in queries)
    assert any("бухгалтерия" in query for query in queries)


def test_cycle_reads_known_message_ids_from_the_intake_ledger():
    assert known_message_ids(
        {"messages": [{"id": "first"}], "ignored_messages": [{"id": "second"}]}
    ) == {"first", "second"}


def test_cycle_keeps_unreadable_messages_out_of_seen_ids_for_retry():
    assert known_message_ids(
        {
            "messages": [],
            "ignored_messages": [],
            "unreadable_messages": [{"id": "retry-me"}],
        }
    ) == set()


def test_cycle_cannot_mark_success_while_recovery_ids_remain():
    assert can_mark_scan_success({"unreadable_messages": []}) is True
    assert can_mark_scan_success({"unreadable_messages": [{"id": "retry-me"}]}) is False


def test_apreal_profile_requires_both_owner_gates_and_browser_recovery():
    profile = ClientProfile.from_json_file(ROOT / "clients" / "ap-real.json")

    assert profile.workflow.owner_approval_required is True
    assert profile.workflow.owner_release_required is True
    assert profile.workflow.client_contact_mode == "manual_owner_release_only"
    assert profile.workflow.message_recovery_mode == "connector_then_main_chrome"
    assert profile.workflow.allow_finance_outreach is False


def test_cycle_records_and_retries_unreadable_message_without_duplicates():
    ledger, created = record_unreadable_message(
        {"messages": [], "ignored_messages": []},
        "retry-me",
        "Invalid IPv6 URL",
        "2026-07-29T10:00:00+03:00",
    )

    assert created is True
    assert ledger["unreadable_messages"] == [
        {
            "id": "retry-me",
            "first_seen_at": "2026-07-29T10:00:00+03:00",
            "last_attempt_at": "2026-07-29T10:00:00+03:00",
            "attempts": 1,
            "error": "Invalid IPv6 URL",
        }
    ]

    ledger, created = record_unreadable_message(
        ledger,
        "retry-me",
        "Invalid IPv6 URL",
        "2026-07-29T10:30:00+03:00",
    )

    assert created is False
    assert ledger["unreadable_messages"][0]["attempts"] == 2
    assert ledger["unreadable_messages"][0]["last_attempt_at"] == "2026-07-29T10:30:00+03:00"


def test_cycle_resolves_quarantined_message_after_successful_read():
    ledger, removed = resolve_unreadable_message(
        {
            "messages": [],
            "ignored_messages": [],
            "unreadable_messages": [{"id": "retry-me"}, {"id": "other"}],
        },
        "retry-me",
    )

    assert removed is True
    assert ledger["unreadable_messages"] == [{"id": "other"}]


def test_cycle_uses_full_window_until_a_successful_scan_is_recorded():
    plan = build_cycle_plan(PROFILE, None)

    assert plan.mode == "bootstrap"
    assert "newer_than:30d" in plan.queries[0]
    assert plan.max_pages == 10


def test_cycle_uses_small_recovery_window_after_successful_scan():
    plan = build_cycle_plan(PROFILE, ScanState(last_success_at="2026-07-27T00:30:00+03:00"))

    assert plan.mode == "incremental"
    assert "newer_than:3d" in plan.queries[0]
    assert plan.max_pages == 3
