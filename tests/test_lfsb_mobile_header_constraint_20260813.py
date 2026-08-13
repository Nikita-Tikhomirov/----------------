from tools.deploy_lfsb_mobile_header_constraint_20260813 import (
    MARKER,
    NEW_STYLE,
    add_header_constraint,
    version_stylesheet,
)


def test_header_constraint_is_added_once() -> None:
    original = b"body { color: #222; }\n"
    once = add_header_constraint(original)
    twice = add_header_constraint(once)

    assert MARKER.encode("ascii") in once
    assert b'.cen_txt > [class^="block"]' in once
    assert b".blok-picture23" in once
    assert b".inf-block" in once
    assert b"height: auto !important" in once
    assert twice == once


def test_stylesheet_version_is_advanced() -> None:
    page = b'<link rel="stylesheet" href="style.css?v=20260813-9">'

    assert NEW_STYLE in version_stylesheet(page)
    assert version_stylesheet(version_stylesheet(page)) == version_stylesheet(page)
