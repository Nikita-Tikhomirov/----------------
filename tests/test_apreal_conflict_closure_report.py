import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_apreal_conflict_closure_report.py"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "build_apreal_conflict_closure_report",
        BUILDER,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_conflict_scope_contains_exactly_the_form_portfolio():
    module = load_builder()

    assert len(module.INCLUDED_SITES) == 30
    assert len(module.EXCLUDED_SITES) == 5
    assert set(module.INCLUDED_SITES).isdisjoint(module.EXCLUDED_SITES)
    assert "apreal.ru" in module.INCLUDED_SITES
    assert "shopap.ru" in module.INCLUDED_SITES
    assert "lic-k.ru" in module.EXCLUDED_SITES


def test_visual_summary_ignores_client_excluded_sites():
    module = load_builder()
    records = [
        {
            "domain": "apreal.ru",
            "type": "custom",
            "viewport": "desktop",
            "status": 200,
            "failures": [],
        },
        {
            "domain": "apreal.ru",
            "type": "custom",
            "viewport": "mobile",
            "status": 200,
            "failures": [],
        },
        {
            "domain": "lic-k.ru",
            "type": "excluded",
            "viewport": "mobile",
            "status": 200,
            "failures": ["legacy console error"],
        },
    ]

    summary = module.summarize_visual_qa(records, {"apreal.ru"})

    assert summary == {
        "sites": 1,
        "views": 2,
        "failed_views": 0,
        "failures": [],
    }


def test_client_email_is_accountable_and_stays_on_the_conflict_scope():
    module = load_builder()
    text = module.build_client_email_text()
    lowered = text.lower()

    assert "предыдущий отчёт прошу не учитывать" in lowered
    assert "это моя ошибка" in lowered
    assert "30 сайтов" in lowered
    assert "две формы" in lowered
    assert "агент" not in lowered
    assert "здоров" not in lowered
    assert "оплат" not in lowered
    assert "видеофон" not in lowered


def test_client_sections_exclude_migration_history():
    module = load_builder()

    assert module.CLIENT_SECTION_TITLES == (
        "Что требовалось исправить",
        "Что сделано",
        "Результаты повторной проверки",
        "Матрица сайтов и получателей",
        "Визуальные подтверждения",
    )
