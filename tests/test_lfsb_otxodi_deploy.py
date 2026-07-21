import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1]
    / "changes"
    / "2026-07-21"
    / "deploy_lfsb_otxodi_feedback.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("deploy_lfsb_otxodi_feedback", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_update_footer_replaces_existing_script_tag_and_preserves_cp1251():
    module = load_module()
    original = (
        '<div>\u041f\u043e\u0434\u0432\u0430\u043b</div>\n'
        '<script src="/client-standard-forms.js" defer></script>\n'
    ).encode("cp1251")

    updated = module.update_footer(original)

    assert updated.decode("cp1251") == (
        '<div>\u041f\u043e\u0434\u0432\u0430\u043b</div>\n'
        '<script src="/client-standard-forms.js?v=20260721-3" defer></script>\n'
    )
