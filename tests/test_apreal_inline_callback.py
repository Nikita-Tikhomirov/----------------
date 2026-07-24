from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "changes" / "2026-07-21" / "apreal.ru"
FRONT_PAGE = SITE / "wp-content" / "themes" / "basic" / "front-page.php"
HANDLER = SITE / "saver2.php"


def test_inline_callback_keeps_fields_inside_infographic() -> None:
    source = FRONT_PAGE.read_text(encoding="utf-8")

    block = source.split('class="text3 info-texts"', 1)[1].split(
        'class="text4 info-texts"', 1
    )[0]

    assert 'id="apreal-inline-callback"' in block
    assert 'name="phone-name"' in block
    assert 'name="phone-phone"' in block
    assert 'href="#cb-sections"' not in block


def test_inline_callback_reports_success_without_navigation() -> None:
    source = FRONT_PAGE.read_text(encoding="utf-8")

    assert "event.preventDefault()" in source
    assert "fetch(form.action" in source
    assert "Спасибо за Ваше сообщение. Оно успешно отправлено" in source
    assert 'class="apreal-inline-callback-close"' in source


def test_inline_callback_close_is_positioned_in_top_right_corner() -> None:
    source = FRONT_PAGE.read_text(encoding="utf-8")

    assert ".apreal-inline-callback-close" in source
    assert "position: absolute" in source
    assert "top: 6px" in source
    assert "right: 8px" in source


def test_inline_callback_preserves_infographic_layout() -> None:
    source = FRONT_PAGE.read_text(encoding="utf-8")

    assert ".text3.info-texts {\n                                position: absolute" in source
    assert "width: 736px" in source
    assert "height: 108px" in source
    assert '#apreal-inline-callback input[type="tel"]' in source
    assert "display: block" in source


def test_inline_callback_uses_stable_aligned_grid() -> None:
    source = FRONT_PAGE.read_text(encoding="utf-8")

    assert "#apreal-inline-callback {" in source
    assert "display: grid;" in source
    assert "grid-template-columns: 240px 240px max-content;" in source
    assert "align-items: end;" in source
    assert "padding: 10px 12px 0;" in source
    assert "position: static !important;" in source
    assert "#apreal-inline-callback .inp3 input[type=\"submit\"]" in source
    assert "height: 42px;" in source


def test_callback_handler_sends_to_site_mailbox_and_returns_json() -> None:
    source = HANDLER.read_text(encoding="utf-8")

    assert "info@apreal.ru" in source
    assert "wp_mail(" in source
    assert "wp_send_json_success" in source
    assert "wp_send_json_error" in source
    assert "phone-phone" in source


def test_callback_handler_remains_compatible_with_legacy_php() -> None:
    source = HANDLER.read_text(encoding="utf-8")

    assert "??" not in source
