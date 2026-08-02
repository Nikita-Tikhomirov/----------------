import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/deploy_apreal_standard_family.py"


def load_module():
    spec = importlib.util.spec_from_file_location("deploy_apreal_standard_family", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_deployment_manifest_covers_the_complete_standard_family():
    module = load_module()
    entries = module.deployment_files(ROOT / "tmp/candidates")

    assert len(entries) == 27
    assert {entry.domain for entry in entries} == {
        "docp.ru",
        "elecktro.ru",
        "medlic.spb.ru",
        "mchs-spb.ru",
        "otxodi.ru",
        "apreal.spb.ru",
        "minkult78.ru",
        "medtex78.ru",
        "mchs78.ru",
        "license39.ru",
        "39mchs.ru",
        "apreal-nn.ru",
        "apreal-volgograd.ru",
        "apreal72.ru",
        "nousro.ru",
        "dpomuc.ru",
        "ed-kgd.ru",
        "muc-vrn.ru",
        "nousro-nn.ru",
        "fste.ru",
        "lfsb.ru",
        "medtex39.ru",
        "shopap.ru",
    }


def test_static_sites_publish_both_script_and_handler():
    module = load_module()
    entries = module.deployment_files(ROOT / "tmp/candidates")

    for domain in module.STATIC_ROOTS:
        names = {entry.remote.name for entry in entries if entry.domain == domain}
        assert names == {"client-standard-forms.js", "client-standard-mail.php"}


def test_snapshot_paths_preserve_domain_and_filename():
    module = load_module()
    entry = next(
        item
        for item in module.deployment_files(ROOT / "tmp/candidates")
        if item.domain == "docp.ru"
    )

    assert module.snapshot_path(ROOT / "tmp/snapshot", entry) == (
        ROOT / "tmp/snapshot/docp.ru/client-standard-forms.php"
    )
