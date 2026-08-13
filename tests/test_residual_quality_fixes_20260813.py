from tools.deploy_residual_quality_fixes_20260813 import (
    CONSTRAINT_MARKER,
    MARKER,
    STYLE_HREF,
    TABLE_OVERRIDE_MARKER,
    VIEWPORT,
    add_responsive_css,
    add_viewport,
    version_stylesheet,
)


def test_add_viewport_preserves_windows_1251_page_and_is_idempotent():
    source = (
        '<meta http-equiv="Content-Type" content="text/html; charset=windows-1251">\r\n'
        '<title>Тест</title>\r\n'
    ).encode("cp1251")

    changed = add_viewport(source)

    assert VIEWPORT.encode("ascii") in changed
    assert changed.decode("cp1251").endswith("<title>Тест</title>\r\n")
    assert add_viewport(changed) == changed


def test_add_viewport_rejects_unknown_template():
    try:
        add_viewport(b"<html><head></head></html>")
    except ValueError as error:
        assert "Content-Type" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_add_responsive_css_is_idempotent():
    changed = add_responsive_css(b"body { color: black; }\n")

    assert MARKER.encode("ascii") in changed
    assert CONSTRAINT_MARKER.encode("ascii") in changed
    assert TABLE_OVERRIDE_MARKER.encode("ascii") in changed
    assert b'table[width="1000"]' in changed
    assert b'table-layout: auto' in changed
    assert add_responsive_css(changed) == changed


def test_version_stylesheet_is_idempotent():
    source = b'<link href="style.css" rel="stylesheet">'

    changed = version_stylesheet(source)

    assert STYLE_HREF.encode("ascii") in changed
    assert version_stylesheet(changed) == changed
