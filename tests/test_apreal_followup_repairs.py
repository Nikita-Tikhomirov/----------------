from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "changes/2026-08-01/followup-repairs"


def test_followup_targets_all_confirmed_domains():
    from tools.deploy_apreal_followup_repairs import (
        candidate_files,
        resource_copies,
    )

    files = candidate_files(CANDIDATES)
    resources = resource_copies()

    assert len(files) == 5
    assert len(resources) == 3
    assert {item.domain for item in (*files, *resources)} == {
        "medlic.spb.ru",
        "nousro.ru",
        "nousro-nn.ru",
        "mca24.ru",
        "medtex39.ru",
    }
    destinations = [item.destination for item in (*files, *resources)]
    assert len(destinations) == len(set(destinations))
    assert str(files[0].destination).endswith(
        "/medlic.spb.ru/public_html/wp-content/mu-plugins/"
        "client-standard-forms.php"
    )

    mca = next(item for item in files if item.domain == "mca24.ru")
    assert str(mca.destination).endswith(
        "/mca24.ru/public_html/wp-content/themes/mca/footer.php"
    )

    medtex = next(
        item
        for item in files
        if item.domain == "medtex39.ru" and item.source.name == "index.html"
    )
    assert str(medtex.destination).endswith(
        "/39mchs.ru/public_html/__shared/medtex39/index.html"
    )

    favicon = next(item for item in resources if item.domain == "medtex39.ru")
    assert str(favicon.source).endswith("/apreal36.ru/public_html/favicon.ico")
    assert str(favicon.destination).endswith(
        "/39mchs.ru/public_html/__shared/medtex39/favicon.ico"
    )


def test_vue_bundle_declares_the_model_used_by_the_legacy_form():
    for domain in ("nousro.ru", "nousro-nn.ru"):
        bundle = (
            CANDIDATES
            / domain
            / "public_html/wp-content/themes/Nousro-theme/js/bundle.js"
        ).read_text(encoding="utf-8")
        assert 'data:{message:"Hello Vue!",toggleOption:"",name:""' in bundle
        assert 'data:{message:"Hello Vue!",name:""' not in bundle


def test_medlic_uses_content_actions_instead_of_chat_overlapped_actions():
    plugin = (
        CANDIDATES / "medlic.spb.ru/client-standard-forms.php"
    ).read_text(encoding="utf-8")

    assert ".csf-actions{display:none!important}" in plugin
    assert ".client-form-actions a:first-child" in plugin
    assert ".client-form-actions a:last-child" in plugin


def test_mca_map_loads_api_and_waits_for_it_before_initialization():
    footer = (
        CANDIDATES
        / "mca24.ru/public_html/wp-content/themes/mca/footer.php"
    ).read_text(encoding="utf-8")

    assert '<script src="https://api-maps.yandex.ru/2.1/' in footer
    assert "if (window.ymaps && typeof window.ymaps.ready === 'function')" in footer
    assert "ymaps.ready(init);" in footer


def test_medtex_map_does_not_reference_missing_marker_or_container():
    page = (CANDIDATES / "medtex39.ru/index.html").read_text(encoding="utf-8")

    assert ".add(myPlacemarkWithContent)" not in page
    assert "new ymaps.Map('map-p'" not in page
    assert "new ymaps.Map('map'" in page


def test_snapshot_path_supports_shared_document_roots(tmp_path):
    from pathlib import PurePosixPath

    from tools.deploy_apreal_followup_repairs import snapshot_local_path

    destination = PurePosixPath(
        "/home/n/nousroc9/39mchs.ru/public_html/__shared/medtex39/index.html"
    )

    assert snapshot_local_path(tmp_path, "medtex39.ru", destination) == (
        tmp_path
        / "medtex39.ru/39mchs.ru/public_html/__shared/medtex39/index.html"
    )


def test_snapshot_downloads_only_uploaded_candidate_files():
    from tools.deploy_apreal_followup_repairs import (
        candidate_files,
        resource_copies,
        snapshot_file_destinations,
    )

    downloads = snapshot_file_destinations(CANDIDATES)

    assert downloads == {item.destination for item in candidate_files(CANDIDATES)}
    assert downloads.isdisjoint(
        {item.destination for item in resource_copies()}
    )
