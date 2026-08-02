import importlib.util
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "changes" / "2026-07-20" / "build_standard_forms.py"
FSA_ROOT = ROOT / "changes" / "2026-07-19" / "fsa-lab.ru"
CUSTOM_DEPLOY = ROOT / "tools" / "deploy_apreal_custom_form_completion.py"
LIVE_ACCEPTANCE = ROOT / "tests" / "live_apreal_portfolio_acceptance.cjs"
SUCCESS = "Спасибо за Ваше сообщение. Оно успешно отправлено"
POLICY = "https://www.apreal.ru/konfedencialnost.html"


def load_generator():
    spec = importlib.util.spec_from_file_location("build_standard_forms", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_custom_deploy():
    spec = importlib.util.spec_from_file_location(
        "deploy_apreal_custom_form_completion",
        CUSTOM_DEPLOY,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_regional_twins_reuse_their_existing_callback_and_question_links():
    module = load_generator()

    for domain in ("39mchs.ru", "minkult78.ru", "medtex78.ru"):
        source = module.render_wordpress_plugin(domain, f"info@{domain}")

        assert 'class="csf-actions"' not in source
        assert "['.js-feedback','callback','ЗАКАЗАТЬ ЗВОНОК']" in source
        assert "['.js-calculate','question','ЗАДАТЬ ВОПРОС']" in source
        assert 'name="email"' not in source


def test_docp_places_both_forms_in_its_existing_sidebar_action_slot():
    module = load_generator()
    source = module.render_wordpress_plugin("docp.ru", "info@docp.ru")

    assert "csf-actions-inline" in source
    assert ".full-navigation" in source
    assert "main,.tm-main .tm-content,.tm-content" in source
    assert "window.matchMedia('(max-width:767px)').matches" in source
    assert "legacy.style.display='none'" in source
    assert 'name="email"' not in source


def test_medtex39_keeps_actions_in_the_existing_page_flow_slot():
    module = load_generator()
    source = module.render_static_script("medtex39.ru")
    handler = module.render_static_handler("medtex39.ru", "info@medtex39.ru")

    assert ".navigation-left.full-navigation" in source
    assert "insertAdjacentElement('afterend',root)" in source
    assert ".csf-actions{position:static" in source
    assert ".csf-actions{position:fixed" not in source
    assert 'name="form_token"' in source
    assert "client-standard-mail.php?challenge=1" in source
    assert "loadChallenge(modal.querySelector('.csf-form'))" in source
    assert 'name="email"' not in source
    assert "CSF_TOKEN_MIN_AGE" in handler
    assert "CSF_RATE_SECONDS" in handler
    assert "verify_challenge();" in handler
    assert "clean_value('name')" in handler
    assert "clean_value('phone')" in handler
    assert "clean_value('question')" in handler
    assert "FILTER_VALIDATE_EMAIL" not in handler


def test_sites_with_one_legacy_action_move_the_pair_into_page_flow():
    module = load_generator()
    expected_targets = {
        "mchs78.ru": ".callback-link",
        "apreal-volgograd.ru": ".eModal-7",
        "dpomuc.ru": ".tm-main .tm-content",
        "elecktro.ru": "#tm-top-b .uk-container",
    }

    for domain, target in expected_targets.items():
        source = module.render_wordpress_plugin(domain, f"info@{domain}")

        assert "csf-actions-inline" in source
        assert target in source
        assert "position:static!important" in source
        assert 'name="email"' not in source


def test_nousro_family_exposes_both_forms_in_existing_header_actions():
    module = load_generator()

    callback_labels = {
        "nousro.ru": "ЗАКАЗАТЬ ЗВОНОК",
        "ed-kgd.ru": "ЗАКАЗАТЬ ЗВОНОК",
        "nousro-nn.ru": "ОТПРАВИТЬ ЗАЯВКУ",
    }
    for domain, callback_label in callback_labels.items():
        source = module.render_wordpress_plugin(domain, f"info@{domain}")

        assert f"['#mail-us','callback','{callback_label}']" in source
        assert "csf-template-question" in source
        assert "questionButton.textContent='ЗАДАТЬ ВОПРОС'" in source
        assert "openModal('question')" in source
        assert "grid-template-columns:repeat(2,minmax(0,1fr))" in source
        assert ".fixed-info__buttons{width:min(100%,420px)!important}" in source

    ed_source = module.render_wordpress_plugin("ed-kgd.ru", "info@ed-kgd.ru")
    assert ".fixed-info__buttons .stacked-buttons>noindex{grid-column:1/-1}" in ed_source


def test_muc_vrn_uses_page_flow_question_on_desktop_and_header_pair_on_mobile():
    module = load_generator()
    source = module.render_wordpress_plugin("muc-vrn.ru", "info@muc-vrn.ru")

    assert "['.fixed-line-right a','callback','ЗАКАЗАТЬ ЗВОНОК']" in source
    assert (
        "['.full-navigation > a[href=\"#modal-full\"]','question','ЗАДАТЬ ВОПРОС']"
        in source
    )
    assert "['.mob-dop-btns a','callback','ЗАКАЗАТЬ ЗВОНОК']" in source
    assert "csf-muc-mobile-question" in source
    assert "mobileQuestion.textContent='ЗАДАТЬ ВОПРОС'" in source
    assert "openModal('question')" in source
    assert (
        "@media(min-width:768px){.csf-muc-mobile-callback,.csf-muc-mobile-question"
        "{display:none!important}}"
        in source
    )


def test_fsa_lab_question_uses_name_phone_and_question_without_email():
    page = (FSA_ROOT / "index.html").read_text(encoding="utf-8")
    handler = (FSA_ROOT / "mail.php").read_text(encoding="utf-8")

    question = page.split('data-form="question"', 1)[1].split("</form>", 1)[0]
    assert 'name="name"' in question
    assert 'name="phone"' in question
    assert 'name="coment"' in question
    assert 'name="email"' not in question

    question_handler = handler.split(
        "} elseif ($form_id === 'question') {",
        1,
    )[1].split("} else {", 1)[0]
    assert "$_POST['name']" in question_handler
    assert "$_POST['phone']" in question_handler
    assert "$_POST['coment']" in question_handler
    assert "$_POST['email']" not in question_handler


def form_blocks(page: str, kind: str) -> list[str]:
    return re.findall(
        rf'<form[^>]+data-form="{kind}"[^>]*>(.*?)</form>',
        page,
        flags=re.DOTALL,
    )


def test_custom_html_forms_share_the_complete_latest_contract():
    pages = (
        ROOT / "changes/2026-07-19/mca24.ru/wp-content/themes/mca/footer.php",
        ROOT / "changes/2026-07-19/med-license.ru/wp-content/themes/license-center/footer.php",
        ROOT / "changes/2026-07-19/mhsl.ru/wp-content/themes/license-center/footer.php",
        ROOT / "changes/2026-07-23/apreal36.ru/deploy/wp-content/themes/basic/footer.php",
        FSA_ROOT / "index.html",
    )

    for path in pages:
        page = path.read_text(encoding="utf-8")
        callbacks = form_blocks(page, "callback")
        questions = form_blocks(page, "question")
        assert callbacks, path
        assert questions, path
        assert "max-height: calc(100vh - 30px)" in page, path
        assert "overflow-y: auto" in page, path

        for callback in callbacks:
            assert re.search(r'name="name"(?![^>]*required)', callback), path
            assert re.search(r'name="phone"[^>]*required', callback), path
            assert re.search(r'name="captcha"[^>]*required', callback), path
            assert 'name="email"' not in callback, path
            assert POLICY in callback, path
            assert SUCCESS in callback, path

        for question in questions:
            assert re.search(r'name="name"(?![^>]*required)', question), path
            assert re.search(r'name="phone"[^>]*required', question), path
            assert re.search(r'name="coment"(?![^>]*required)', question), path
            assert re.search(r'name="captcha"[^>]*required', question), path
            assert 'name="email"' not in question, path
            assert POLICY in question, path
            assert SUCCESS in question, path


def test_custom_html_handlers_accept_optional_names_and_require_captcha():
    handlers = (
        ROOT / "changes/2026-07-19/mca24.ru/mail.php",
        ROOT / "changes/2026-07-19/med-license.ru/mail.php",
        ROOT / "changes/2026-07-19/mhsl.ru/mail.php",
        ROOT / "changes/2026-07-23/apreal36.ru/deploy/mail.php",
        FSA_ROOT / "mail.php",
    )

    for path in handlers:
        source = path.read_text(encoding="utf-8")
        callback = source.split("if ($form_id === 'callback') {", 1)[1].split(
            "} elseif ($form_id === 'question') {",
            1,
        )[0]
        question = source.split("} elseif ($form_id === 'question') {", 1)[1].split(
            "} else {",
            1,
        )[0]
        assert "$_POST['name']" in callback, path
        assert "$_POST['phone']" in callback, path
        assert "Введите имя" not in callback, path
        assert "$_POST['name']" in question, path
        assert "$_POST['phone']" in question, path
        assert "$_POST['coment']" in question, path
        assert "Введите имя" not in question, path
        assert "isset($_POST['captcha']) &&" not in source, path
        assert SUCCESS in source, path


def test_custom_handlers_align_domain_sender_and_reply_to():
    wordpress_handlers = (
        ROOT / "changes/2026-07-19/mca24.ru/mail.php",
        ROOT / "changes/2026-07-19/med-license.ru/mail.php",
        ROOT / "changes/2026-07-19/mhsl.ru/mail.php",
        ROOT / "changes/2026-07-23/apreal36.ru/deploy/mail.php",
    )
    for path in wordpress_handlers:
        source = path.read_text(encoding="utf-8")
        assert "'Reply-To: ' . APREAL_FORM_SENDER" in source, path
        assert "function apreal_form_set_envelope_sender($phpmailer)" in source, path
        assert "$phpmailer->Sender = $phpmailer->From;" in source, path
        assert "add_action('phpmailer_init', 'apreal_form_set_envelope_sender', 999);" in source, path
        assert "remove_action('phpmailer_init', 'apreal_form_set_envelope_sender', 999);" in source, path

    static_handler = (FSA_ROOT / "mail.php").read_text(encoding="utf-8")
    assert "'Reply-To: ' . APREAL_FORM_SENDER" in static_handler
    assert "'-f' . APREAL_FORM_SENDER" in static_handler


def test_cf7_custom_sites_use_the_same_name_phone_question_contract():
    module = load_custom_deploy()

    for site, forms in module.CF7_FORMS.items():
        callback = forms["callback"]["form"]
        question = forms["question"]["form"]
        assert "[text " in callback, site
        assert "[tel* " in callback, site
        assert "Введите цифрами: пять|5" in callback, site
        assert "[email" not in callback, site
        assert POLICY in callback, site
        assert "[text " in question, site
        assert "[tel* " in question, site
        assert "[textarea " in question, site
        assert "Введите цифрами: пять|5" in question, site
        assert "[email" not in question, site
        assert POLICY in question, site
        assert forms["callback"]["success"] == SUCCESS
        assert forms["question"]["success"] == SUCCESS


def test_cf7_sites_align_sender_reply_to_and_envelope_sender():
    module = load_custom_deploy()

    for domain, forms in module.CF7_FORMS.items():
        expected = f"wordpress@{domain}"
        for kind in ("callback", "question"):
            mail = forms[kind]["mail"]
            assert expected in mail["sender"]
            assert mail["additional_headers"] == f"Reply-To: {expected}"

        plugin = next(
            item["source"]
            for item in module.deployment_files()
            if item["domain"] == domain
            and item["remote"].name == "client-form-envelope-sender.php"
        )
        source = plugin.read_text(encoding="utf-8")
        assert f"const APREAL_FORM_ENVELOPE_SENDER = '{expected}';" in source
        assert "$phpmailer->Sender = $phpmailer->From;" in source
        assert "add_action('phpmailer_init'" in source


def test_live_acceptance_rejects_inexact_action_and_modal_titles():
    source = LIVE_ACCEPTANCE.read_text(encoding="utf-8")

    assert "EXPECTED_ACTION_LABELS" in source
    assert "trigger label mismatch" in source
    assert "modal title mismatch" in source
