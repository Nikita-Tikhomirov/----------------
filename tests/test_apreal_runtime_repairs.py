from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "changes/2026-08-01/runtime-repairs"


def test_runtime_candidates_cover_every_confirmed_source_error():
    from tools.deploy_apreal_runtime_repairs import deployment_files

    files = deployment_files(CANDIDATES)
    assert len(files) == 16
    assert {item.domain for item in files} == {
        "apreal.ru",
        "apreal-volgograd.ru",
        "apreal36.ru",
        "docp.ru",
        "fsa-lab.ru",
        "lfsb.ru",
        "mchs78.ru",
        "medlic.spb.ru",
        "muc-vrn.ru",
        "nousro-nn.ru",
        "nousro-spb.ru",
        "nousro.ru",
    }
    assert all(item.source.is_file() for item in files)


def test_runtime_candidates_contain_the_root_cause_repairs():
    def text(relative: str) -> str:
        return (CANDIDATES / relative).read_text(encoding="utf-8")

    docp = text(
        "docp.ru/public_html/wp-content/themes/apreal-Lic-master/footer.php"
    )
    assert ".add(myPlacemarkWithContent)" not in docp

    apreal = text("apreal.ru/public_html/wp-content/themes/basic/footer.php")
    assert "};\n    objectManager.add(data);" in apreal
    apreal_functions = text(
        "apreal.ru/public_html/wp-content/themes/basic/functions.php"
    )
    assert "js/popper.min.js" not in apreal_functions

    apreal36 = text(
        "apreal36.ru/public_html/wp-content/themes/basic/functions.php"
    )
    assert "wp_enqueue_script( 'jquery' );" in apreal36

    for domain in ("nousro.ru", "nousro-nn.ru"):
        page = text(
            f"{domain}/public_html/wp-content/themes/Nousro-theme/"
            "components/front-page.inc.php"
        )
        assert "toggleOption: ''," in page
        assert "if (!window.Vue" in page
        assert ".aos-init.aos-animate" not in page

    fsa = text("fsa-lab.ru/public_html/index.html")
    assert 'class="modal-trigger open-question"' not in fsa

    mchs_functions = text(
        "mchs78.ru/public_html/wp-content/themes/MCHS/functions.php"
    )
    assert "material_js" in mchs_functions
    assert "/build/css/main.css" not in mchs_functions
    mchs_footer = text("mchs78.ru/public_html/wp-content/themes/MCHS/footer.php")
    assert (
        '<script src="/design/vendor/jquery-form-validator/form-validator/'
        'jquery.form-validator.min.js"></script>'
    ) in mchs_footer

    medlic = text(
        "medlic.spb.ru/public_html/wp-content/themes/yoo_nano3_wp/"
        "layouts/theme.config.php"
    )
    assert "addFile('js', 'js:uikit.js')" not in medlic

    muc_header = text(
        "muc-vrn.ru/public_html/wp-content/themes/MUC-VRN/header.php"
    )
    muc_footer = text(
        "muc-vrn.ru/public_html/wp-content/themes/MUC-VRN/footer.php"
    )
    assert muc_header.count('var n = d.getElementsByTagName("script")') == 1
    assert 'var n = document.getElementsByTagName("script")' in muc_header
    assert "if (framePoster)" in muc_footer
    assert "if (document.getElementById('map-p'))" in muc_footer

    spb = text(
        "nousro-spb.ru/public_html/wp-content/themes/Nousro-theme/footer.php"
    )
    assert "if (currentMenuItem)" in spb

    lfsb = text("lfsb.ru/public_html/style.css")
    assert "bg-center.jpg" not in lfsb

    volgograd = text(
        "apreal-volgograd.ru/public_html/wp-content/themes/"
        "yoo_eat_wp/layouts/theme.php"
    )
    assert "user.profitmore.ru" not in volgograd
    assert "data:text/javascript;charset=utf-8;base64" not in volgograd


def test_runtime_deploy_can_isolate_one_domain():
    from tools.deploy_apreal_runtime_repairs import (
        deployment_files,
        resource_copies,
    )

    files = deployment_files(CANDIDATES, {"apreal-volgograd.ru"})
    resources = resource_copies({"apreal-volgograd.ru"})

    assert [item.domain for item in files] == ["apreal-volgograd.ru"]
    assert resources == ()


def test_nousro_spb_runtime_deploy_includes_theme_and_label_plugin():
    from tools.deploy_apreal_runtime_repairs import deployment_files

    files = deployment_files(CANDIDATES, {"nousro-spb.ru"})

    assert [item.destination.name for item in files] == [
        "footer.php",
        "nousro-spb-question-fix.php",
    ]
    assert files[1].source == (
        ROOT / "changes/2026-07-22/nousro-spb-question-fix.php"
    )


def test_resource_recovery_covers_every_observed_first_party_404():
    from tools.deploy_apreal_runtime_repairs import resource_copies

    copies = resource_copies()
    assert len(copies) == 65
    destinations = [item.destination for item in copies]
    assert len(destinations) == len(set(destinations))
    assert {item.domain for item in copies} == {
        "39mchs.ru",
        "apreal-nn.ru",
        "apreal.ru",
        "apreal72.ru",
        "license39.ru",
        "medtex78.ru",
        "minkult78.ru",
    }


def test_snapshot_paths_cannot_escape_the_snapshot_root(tmp_path):
    from tools.deploy_apreal_runtime_repairs import (
        deployment_files,
        resource_copies,
        snapshot_path,
    )

    for item in (*deployment_files(CANDIDATES), *resource_copies()):
        target = snapshot_path(tmp_path, item.domain, item.destination)
        assert target.is_relative_to(tmp_path)
        assert target.parts[-2:] != ("..", target.name)


def test_resume_accepts_only_snapshot_or_candidate_state():
    from tools.deploy_apreal_runtime_repairs import classify_resume_state

    snapshot = {"exists": True, "size": 3, "sha256": "old"}
    candidate = {"exists": True, "size": 3, "sha256": "new"}

    assert classify_resume_state(snapshot, snapshot, candidate, "/old") == "snapshot"
    assert classify_resume_state(candidate, snapshot, candidate, "/new") == "candidate"

    with pytest.raises(RuntimeError, match="Unexpected live state"):
        classify_resume_state(
            {"exists": True, "size": 5, "sha256": "other"},
            snapshot,
            candidate,
            "/other",
        )
