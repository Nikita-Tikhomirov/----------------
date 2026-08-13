from tools.deploy_lfsb_runtime_cleanup_20260813 import clean_page


def test_clean_directory_pages_use_local_jquery():
    source = b'<script src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>'

    for name in ("fstec_dir.php", "kripto_dir.php"):
        changed = clean_page(name, source)
        assert b'/js/jquery-latest.js' in changed
        assert b'http://ajax.googleapis.com' not in changed


def test_clean_contact_page_uses_https_map_api():
    source = (
        b'http://api-maps.yandex.ru/2.0-stable/?onload=x '
        b'http://api.yandex.ru/maps/tools/constructor/index.xml'
    )

    changed = clean_page("contakt.php", source)

    assert b'https://api-maps.yandex.ru/2.0-stable/' in changed
    assert b'https://api.yandex.ru/maps/tools/constructor/index.xml' in changed


def test_clean_send_page_removes_missing_scripts_and_uses_local_jquery():
    source = (
        b'<script src="ds.js" type="text/javascript"></script>\r\n'
        b'<script src="nk.js" type="text/javascript"></script>\r\n'
        b'<script src="http://ajax.googleapis.com/ajax/libs/jquery/1/jquery.min.js"></script>\r\n'
    )

    changed = clean_page("sendlic.php", source)

    assert b'ds.js' not in changed
    assert b'nk.js' not in changed
    assert b'/js/jquery-latest.js' in changed
