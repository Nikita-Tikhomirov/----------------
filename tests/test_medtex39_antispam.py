from pathlib import Path


ROOT = (
    Path(__file__).resolve().parents[1]
    / "changes"
    / "2026-07-22"
    / "medtex39.ru"
    / "deploy"
)


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_legacy_handler_is_retired_without_sending_mail():
    source = read("tomt_dir.php")

    assert "http_response_code(410)" in source
    assert "mail(" not in source
    assert "client-standard-mail.php" in source


def test_active_handler_requires_a_session_challenge():
    source = read("client-standard-mail.php")

    assert "session_start()" in source
    assert "$_GET['challenge']" in source
    assert "random_bytes(" in source
    assert "hash_equals(" in source
    assert "clean_value('form_token')" in source
    assert "CSF_TOKEN_MIN_AGE" in source
    assert "CSF_TOKEN_MAX_AGE" in source
    assert "unset($_SESSION['csf_form_token']" in source


def test_active_handler_rejects_non_phone_values():
    source = read("client-standard-mail.php")

    assert "preg_replace('/\\D+/" in source
    assert "strlen($phone_digits) < 7" in source
    assert "strlen($phone_digits) > 18" in source


def test_frontend_requests_and_submits_the_challenge():
    source = read("client-standard-forms.js")

    assert 'name="form_token"' in source
    assert "?challenge=1" in source
    assert "loadChallenge(form)" in source
    assert "form_token" in source
    assert "html.client-contact-modal-open body > jdiv" in source
    assert "classList.add('client-contact-modal-open')" in source
    assert ".csf-actions{position:static" in source
    assert "document.querySelector('.navigation-left.full-navigation')" in source


def test_index_uses_cache_busted_antispam_bundle():
    source = read("index.html")

    assert 'client-standard-forms.js?v=20260722-1' in source
