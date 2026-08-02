from pathlib import PurePosixPath


def test_moopb_redirect_stays_on_https():
    from tools.deploy_apreal_migration_repairs import (
        repair_moopb_htaccess,
        repair_moopb_style,
    )

    original = b"RewriteRule ^(.*)$ http://www.moopb.ru/$1 [R=301,L]\r\n"

    repaired = repair_moopb_htaccess(original)

    assert b"https://www.moopb.ru/$1" in repaired
    assert b"http://www.moopb.ru/$1" not in repaired

    style = repair_moopb_style(b"body { color: #000; }\n")
    assert b"AP-REAL-MOOPB-MOBILE-REPAIR" in style
    assert b"@media (max-width: 767px)" in style
    assert b"table-layout: fixed !important" in style


def test_electro_reg_mobile_layout_contains_long_content():
    from tools.deploy_apreal_migration_repairs import (
        repair_electro_reg_config,
        repair_electro_reg_style,
    )

    style = repair_electro_reg_style(b"/* existing custom styles */\n")

    assert b"AP-REAL-ELECTRO-MOBILE-REPAIR" in style
    assert b"#n2-ss-4item1" in style
    assert b"ul.uk-tab.uk-tab-grid" in style
    assert b"flex-direction: column !important" in style
    assert b"overflow-x: hidden !important" in style

    config = repair_electro_reg_config(
        b"$this['asset']->addFile('css', 'css:custom.css');\n"
    )
    assert b"get_template_directory_uri()" in config
    assert b"custom.css?v=20260802" in config


def test_ohrana_slider_ignores_pages_without_slider_markup():
    from tools.deploy_apreal_migration_repairs import repair_ohrana_slider

    original = (
        b"function slider(target,showfirst) {\n"
        b" var slider = document.getElementById(target);\n"
        b" var divs = slider.getElementsByTagName('div');\n"
        b"}\n"
    )

    repaired = repair_ohrana_slider(original)

    assert b"if (!slider)" in repaired
    assert repaired.index(b"if (!slider)") < repaired.index(b"getElementsByTagName")


def test_ohrana_assets_are_local_and_https_only():
    from tools.deploy_apreal_migration_repairs import (
        repair_ohrana_fonts,
        repair_ohrana_html,
        repair_ohrana_style,
    )

    fonts = repair_ohrana_fonts(
        b"url(http://fonts.gstatic.com/s/ptsans/v8/font.woff) format('woff')"
    )
    style = repair_ohrana_style(
        b'url("https://nousro.ru/bitrix/templates/content/img/icon_folder.png")'
    )
    html = repair_ohrana_html(
        b'http://counter.rambler.ru/top100.jcn http://top100.rambler.ru/navi/'
    )

    assert b"../fonts/PTS55F-webfont.woff" in fonts
    assert b"fonts.gstatic.com" not in fonts
    assert b'../images/icon_folder.png' in style
    assert b"nousro.ru/bitrix" not in style
    assert b"AP-REAL-MOBILE-REPAIR" in style
    assert b"@media (max-width: 767px)" in style
    assert b"min-width: 0 !important" in style
    assert b"http://counter.rambler.ru" not in html
    assert b"http://top100.rambler.ru" not in html
    assert b"https://counter.rambler.ru" in html
    assert b"https://top100.rambler.ru" in html


def test_repair_manifest_targets_only_confirmed_files():
    from tools.deploy_apreal_migration_repairs import remote_targets

    targets = remote_targets()
    destinations = {item.destination for item in targets}

    assert PurePosixPath(
        "/home/n/nousroc9/moopb.ru/public_html/.htaccess"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/moopb.ru/public_html/ssi/right.php"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/moopb.ru/public_html/style.css"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/ohrana-truda.nousro.ru/public_html/scripts/slider1.js"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/ohrana-truda.nousro.ru/public_html/css/css.css"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/ohrana-truda.nousro.ru/public_html/css/style.css"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/ohrana-truda.nousro.ru/public_html/images/icon_folder.png"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/electro-reg.ru/public_html/"
        "wp-content/themes/yoo_finch_wp/css/custom.css"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/electro-reg.ru/public_html/"
        "wp-content/themes/yoo_finch_wp/layouts/theme.config.php"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/rectavr.ru/public_html/wp-content/themes/miteri/style.css"
    ) in destinations
    assert PurePosixPath(
        "/home/n/nousroc9/mchs-vrn.ru/public_html/"
        "wp-content/themes/license-center/css/style.css"
    ) in destinations
    assert len(targets) == 21


def test_ohrana_html_repairs_legacy_plugin_order_and_broken_widgets():
    from tools.deploy_apreal_migration_repairs import repair_ohrana_html

    original = b"""
<!-- Add fancyBox main JS and CSS files -->
<script type="text/javascript" src="scripts/jquery_003.js"></script>
<link href="scripts/style_002.css" type="text/css" rel="Stylesheet">
<script src="scripts/jquery_002.js" type="text/javascript"></script>
<script async type="text/javascript" src="highslide/highslide.js"></script>
<script language="javascript" type="text/javascript">
<!--
hs.graphicsDir = 'highslide/graphics/';
hs.outlineType = 'rounded-white';
//-->
</script>
<a href="certificate.jpg" onclick="return hs.expand(this)">certificate</a>
<!-- Yandex.Metrika informer -->
<img src="//bs.yandex.ru/informer/15488413/test">
<!-- /Yandex.Metrika informer -->
http://counter.rambler.ru/x http://top100.rambler.ru/x
"""

    repaired = repair_ohrana_html(original)

    main_marker = b'<script type="text/javascript" src="scripts/jquery_002.js">'
    carousel_marker = b'<script src="scripts/jquery_003.js" type="text/javascript">'
    assert main_marker in repaired
    assert carousel_marker in repaired
    assert b"highslide.js" not in repaired
    assert b"hs.expand" not in repaired
    assert b'target="_blank" rel="noopener"' in repaired
    assert b"bs.yandex.ru/informer" not in repaired


def test_rectavr_mobile_branding_does_not_force_a_750px_page():
    from tools.deploy_apreal_migration_repairs import repair_rectavr_style

    style = repair_rectavr_style(b"/* existing theme metadata */\n")

    assert b"AP-REAL-RECTAVR-MOBILE-REPAIR-V3" in style
    assert b".site-branding .left-brand" in style
    assert b"min-width: 0 !important" in style
    assert b"max-width: 100% !important" in style
    assert b".site-title-centered .site-title" in style
    assert b"width: 100% !important" in style
    assert b"text-align: center" in style


def test_mchs_vrn_mobile_banner_stays_inside_the_viewport():
    from tools.deploy_apreal_migration_repairs import repair_mchs_vrn_style

    style = repair_mchs_vrn_style(b"/* existing theme styles */\n")

    assert b"AP-REAL-MCHS-VRN-MOBILE-REPAIR" in style
    assert b".section-banner__title" in style
    assert b"font-size: 32px" in style
    assert b"word-break: normal" in style
    assert b".section-banner__text" in style
    assert b"width: auto !important" in style
    assert b"max-width: 100% !important" in style
    assert b"overflow-x: hidden !important" in style
