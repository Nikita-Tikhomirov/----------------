import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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
            "body": "Бухгалтерия подтверждает оплату",
            "attachments": [],
        },
    )

    assert decision.bucket == "finance"
    assert decision.requires_technical_task is False


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

    assert "is:unread in:inbox" in queries
    assert any("nousro-nn.ru" in query for query in queries)
    assert any("бухгалтерия" in query for query in queries)
