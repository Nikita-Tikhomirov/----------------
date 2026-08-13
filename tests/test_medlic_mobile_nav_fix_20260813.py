from tools.deploy_medlic_mobile_nav_fix_20260813 import MARKER, add_mobile_nav_rule


def test_add_mobile_nav_rule_is_scoped_and_idempotent():
    source = b"<style>.existing{display:block}</style>"

    changed = add_mobile_nav_rule(source)

    assert MARKER.encode("ascii") in changed
    assert b"@media (max-width:767px)" in changed
    assert b".navigation.green>ul>li>ul" in changed
    assert add_mobile_nav_rule(changed) == changed


def test_add_mobile_nav_rule_requires_style_block():
    try:
        add_mobile_nav_rule(b"<?php echo 'missing';")
    except ValueError as error:
        assert "style" in str(error).lower()
    else:
        raise AssertionError("Expected ValueError")
