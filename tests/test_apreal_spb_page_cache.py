import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "changes"
    / "2026-07-24"
    / "purge_apreal_spb_page_cache.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("purge_apreal_spb_page_cache", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cache_purge_is_scoped_to_apreal_spb_page_cache():
    module = load_module()

    assert str(module.HOME) == "/home/n/nousroc9"
    assert str(module.CACHE_ROOT) == (
        "/home/n/nousroc9/apreal.spb.ru/public_html/"
        "wp-content/cache/page_enhanced/apreal.spb.ru"
    )
    assert module.CACHE_ROOT.parent.name == "page_enhanced"
    assert module.CACHE_ROOT.name == "apreal.spb.ru"
