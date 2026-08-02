import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "changes"
    / "2026-07-20"
    / "build_standard_forms.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("build_standard_forms", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StandardFormGeneratorTests(unittest.TestCase):
    def test_wordpress_plugin_contains_required_contract(self):
        module = load_module()
        source = module.render_wordpress_plugin("example.ru", "info@example.ru")

        self.assertIn("info@example.ru", source)
        self.assertIn("ЗАКАЗАТЬ ЗВОНОК", source)
        self.assertIn("ЗАДАТЬ ВОПРОС", source)
        self.assertIn("name=\"phone\"", source)
        self.assertNotIn("name=\"email\"", source)
        self.assertIn("name=\"captcha\"", source)
        self.assertIn(
            'Нажимая на кнопку "Отправить" я даю согласие на обработку '
            "персональных данных на условиях",
            source,
        )
        self.assertIn("Политики обработки персональных данных", source)
        self.assertIn(module.POLICY_URL, source)
        self.assertIn(module.SUCCESS_MESSAGE, source)
        self.assertIn("check_ajax_referer", source)

        question_handler = source.split(
            "} elseif ($kind === 'question') {",
            1,
        )[1].split("} else {", 1)[0]
        self.assertIn("csf_clean_text('name')", question_handler)
        self.assertIn("csf_clean_text('phone')", question_handler)
        self.assertIn("csf_clean_text('question')", question_handler)
        self.assertIn("if ($phone === '')", question_handler)
        self.assertNotIn("email", question_handler.lower())

        question_form = source.split('data-modal="question"', 1)[1]
        self.assertTrue(
            question_form.index('name="name"')
            < question_form.index('name="phone"')
            < question_form.index('name="question"')
            < question_form.index('name="captcha"')
        )

    def test_static_bundle_uses_domain_recipient(self):
        module = load_module()
        handler = module.render_static_handler("example.ru", "help@example.ru")
        script = module.render_static_script("example.ru")

        self.assertIn("help@example.ru", handler)
        self.assertIn("wordpress@example.ru", handler)
        self.assertIn("$_POST['name']", handler)
        self.assertIn("<strong>Имя:</strong>", handler)
        self.assertIn(module.SUCCESS_MESSAGE, handler)
        self.assertIn(module.POLICY_URL, script)
        self.assertIn("client-standard-mail.php", script)

        callback_name = script.index('name="name"')
        callback_phone = script.index('name="phone"')
        self.assertLess(callback_name, callback_phone)

        question_form = script[script.index('data-modal="question"'):]
        self.assertTrue(
            question_form.index('name="name"')
            < question_form.index('name="phone"')
            < question_form.index('name="question"')
            < question_form.index('name="captcha"')
        )
        self.assertNotIn('name="email"', question_form)
        question_handler = handler.split(
            "} elseif ($kind === 'question') {",
            1,
        )[1].split("} else {", 1)[0]
        self.assertIn("$_POST['name']", question_handler)
        self.assertIn("$_POST['phone']", question_handler)
        self.assertIn("$_POST['question']", question_handler)
        self.assertIn("if ($phone === '')", question_handler)
        self.assertNotIn("email", question_handler.lower())
        self.assertIn("\\u043f\\u043e\\u0434\\u0430\\u0442\\u044c", script)
        self.assertIn("csf-actions-sidebar", script)
        self.assertIn("document.querySelector('#leblok')", script)
        self.assertNotIn("csf-actions-has-legacy-callback", script)

    def test_wordpress_handler_aligns_from_reply_to_and_envelope_sender(self):
        module = load_module()
        source = module.render_wordpress_plugin("mchs78.ru", "info@mchs78.ru")

        self.assertIn("'Reply-To: ' . CSF_SENDER", source)
        self.assertIn("function csf_set_envelope_sender($phpmailer)", source)
        self.assertIn("$phpmailer->Sender = $phpmailer->From;", source)
        self.assertIn(
            "add_action('phpmailer_init', 'csf_set_envelope_sender', 999);",
            source,
        )
        self.assertIn(
            "remove_action('phpmailer_init', 'csf_set_envelope_sender', 999);",
            source,
        )

    def test_static_handler_aligns_from_reply_to_and_envelope_sender(self):
        module = load_module()
        for domain in module.STATIC_SITES:
            source = module.render_static_handler(domain, f"info@{domain}")
            self.assertIn("'Reply-To: ' . CSF_SENDER", source, domain)
            self.assertIn("'-f' . CSF_SENDER", source, domain)

    def test_lfsb_uses_existing_sidebar_button_location(self):
        module = load_module()
        script = module.render_static_script("lfsb.ru")

        self.assertIn("legacyCallbackAnchor", script)
        self.assertIn("document.querySelector('#leblok,#le5')", script)
        self.assertIn("legacyCallbackAnchor.style.display='none'", script)

    def test_otxodi_uses_existing_header_buttons_only(self):
        module = load_module()
        otxodi = module.render_wordpress_plugin("otxodi.ru", "info@otxodi.ru")
        ordinary = module.render_wordpress_plugin("example.ru", "info@example.ru")

        self.assertIn(".csf-actions{display:none!important}", otxodi)
        self.assertIn(".header-top .calc-button{cursor:pointer", otxodi)
        self.assertIn(".header-top .calc-button:hover", otxodi)
        self.assertIn(".header-top .calc-button:focus-visible", otxodi)
        self.assertIn(".header-top .calc-button", otxodi)
        self.assertIn(".header-top .backform", otxodi)
        self.assertIn("csf-actions-mobile", otxodi)
        self.assertIn("insertAdjacentElement('afterend'", otxodi)
        self.assertNotIn(".csf-actions{display:none!important}", ordinary)

    def test_mchs_spb_matches_the_accepted_otxodi_form_contract(self):
        module = load_module()
        source = module.render_wordpress_plugin(
            "mchs-spb.ru",
            "info@mchs-spb.ru",
        )

        self.assertIn("const CSF_RECIPIENT = 'info@mchs-spb.ru';", source)
        self.assertIn(".csf-actions{display:none!important}", source)
        self.assertIn(".header-top .calc-button", source)
        self.assertIn(".header-top .backform", source)
        self.assertIn("csf-actions-mobile", source)

    def test_medlic_uses_existing_content_buttons_without_chat_overlap(self):
        module = load_module()
        source = module.render_wordpress_plugin(
            "medlic.spb.ru",
            "info@medlic.spb.ru",
        )

        self.assertIn(".csf-actions{display:none!important}", source)
        self.assertIn(
            "['.client-form-actions a:first-child','callback','ЗАКАЗАТЬ ЗВОНОК']",
            source,
        )
        self.assertIn(
            "['.client-form-actions a:last-child','question','ЗАДАТЬ ВОПРОС']",
            source,
        )

        question_form = source.split('data-modal="question"', 1)[1]
        self.assertTrue(
            question_form.index('name="name"')
            < question_form.index('name="phone"')
            < question_form.index('name="question"')
            < question_form.index('name="captcha"')
        )
        self.assertNotIn('name="email"', question_form)

        self.assertIn(
            "#n2-ss-2.n2-ss-load-fade.n2-ss-loaded{opacity:1!important}",
            source,
        )
        ordinary = module.render_wordpress_plugin(
            "example.ru",
            "info@example.ru",
        )
        self.assertNotIn("#n2-ss-2.n2-ss-load-fade", ordinary)

    def test_docp_places_standard_actions_in_the_existing_sidebar_slot(self):
        module = load_module()
        source = module.render_wordpress_plugin("docp.ru", "info@docp.ru")

        self.assertIn("csf-actions-inline", source)
        self.assertIn("const CSF_CENTRAL_RECIPIENT = 'upreal@bk.ru';", source)
        self.assertIn("'Bcc: ' . CSF_CENTRAL_RECIPIENT", source)
        self.assertIn("document.querySelector('.full-navigation')", source)
        self.assertIn("legacy.style.display='none'", source)
        self.assertIn('data-modal="callback"', source)
        self.assertIn('data-modal="question"', source)

    def test_central_copy_is_limited_to_failed_delivery_routes(self):
        module = load_module()
        expected = {
            "39mchs.ru",
            "docp.ru",
            "dpomuc.ru",
            "ed-kgd.ru",
            "minkult78.ru",
            "muc-vrn.ru",
            "nousro.ru",
            "nousro-nn.ru",
        }

        self.assertEqual(module.CENTRAL_COPY_SITES, expected)
        selected = module.render_wordpress_plugin("dpomuc.ru", "info@dpomuc.ru")
        ordinary = module.render_wordpress_plugin("otxodi.ru", "info@otxodi.ru")
        self.assertIn("const CSF_CENTRAL_RECIPIENT = 'upreal@bk.ru';", selected)
        self.assertNotIn("CSF_CENTRAL_RECIPIENT", ordinary)

    def test_unreliable_bcc_routes_send_the_central_copy_separately(self):
        module = load_module()

        self.assertEqual(
            module.SEPARATE_CENTRAL_COPY_SITES,
            {"39mchs.ru", "muc-vrn.ru"},
        )
        for domain in module.SEPARATE_CENTRAL_COPY_SITES:
            source = module.render_wordpress_plugin(
                domain,
                module.WORDPRESS_SITES[domain],
            )
            self.assertNotIn("'Bcc: ' . CSF_CENTRAL_RECIPIENT", source, domain)
            self.assertIn("if (!$sent || !$central_sent)", source, domain)

        muc_source = module.render_wordpress_plugin(
            "muc-vrn.ru",
            module.WORDPRESS_SITES["muc-vrn.ru"],
        )
        self.assertIn(
            "$central_sent = wp_mail(CSF_CENTRAL_RECIPIENT, $subject, $message, $headers);",
            muc_source,
        )

        plain_source = module.render_wordpress_plugin(
            "39mchs.ru",
            module.WORDPRESS_SITES["39mchs.ru"],
        )
        self.assertIn("$central_message = preg_replace", plain_source)
        self.assertIn("wp_strip_all_tags($central_message)", plain_source)
        self.assertIn("$central_headers = array(", plain_source)
        self.assertIn(
            "$central_sent = wp_mail(CSF_CENTRAL_RECIPIENT, $subject, $central_message, $central_headers);",
            plain_source,
        )
        self.assertLess(
            plain_source.index("$central_sent = wp_mail("),
            plain_source.index("$sent = wp_mail(CSF_RECIPIENT"),
        )

    def test_apreal_spb_uses_existing_buttons_with_correct_form_kinds(self):
        module = load_module()
        source = module.render_wordpress_plugin("apreal.spb.ru", "spb@apreal.ru")

        self.assertIn("const CSF_SENDER = 'wordpress@apreal.spb.ru';", source)
        self.assertIn(".csf-actions{display:none!important}", source)
        self.assertIn(".phones .phones__callback", source)
        self.assertIn(".ap-mobile-navs .phones__callback", source)
        self.assertIn(".custom-slider .phones__callback", source)
        self.assertIn(".uk-width-expand\\\\@m.notForCopy .phones__callback", source)
        self.assertIn(".uk-width-1-6\\\\@m .uk-button-danger", source)
        self.assertIn("el.dataset.csfBound='1'", source)
        self.assertIn("if(el.dataset.csfBound==='1')return", source)
        self.assertIn("['.phones .phones__callback','callback','ЗАКАЗАТЬ ЗВОНОК']", source)
        self.assertIn("['.custom-slider .phones__callback','question','ЗАДАТЬ ВОПРОС']", source)

        question_form = source.split('data-modal="question"', 1)[1]
        self.assertTrue(
            question_form.index('name="name"')
            < question_form.index('name="phone"')
            < question_form.index('name="question"')
            < question_form.index('name="captcha"')
        )
        self.assertNotIn('name="email"', question_form)

    def test_license39_uses_its_existing_buttons_with_correct_form_kinds(self):
        module = load_module()
        source = module.render_wordpress_plugin("license39.ru", "info@license39.ru")

        self.assertIn("const CSF_SENDER = 'info@license39.ru';", source)
        self.assertIn(".csf-actions{display:none!important}", source)
        self.assertIn("['.phones .phones__callback','callback','ЗАКАЗАТЬ ЗВОНОК']", source)
        self.assertIn("['.ap-mobile-navs .phones__callback','callback','ЗАКАЗАТЬ ЗВОНОК']", source)
        self.assertIn("['.custom-slider .phones__callback','question','ЗАДАТЬ ВОПРОС']", source)
        self.assertIn(
            "['.uk-width-1-6\\\\@m .uk-button-danger','question','ЗАДАТЬ ВОПРОС']",
            source,
        )
        self.assertIn("el.dataset.csfBound='1'", source)
        self.assertIn("if(el.dataset.csfBound==='1')return", source)

        question_form = source.split('data-modal="question"', 1)[1]
        self.assertTrue(
            question_form.index('name="name"')
            < question_form.index('name="phone"')
            < question_form.index('name="question"')
            < question_form.index('name="captcha"')
        )
        self.assertNotIn('name="email"', question_form)

    def test_apreal_nn_maps_legacy_modal_links_to_standard_forms(self):
        module = load_module()
        source = module.render_wordpress_plugin("apreal-nn.ru", "info@apreal-nn.ru")

        self.assertIn("const CSF_SENDER = 'info@apreal-nn.ru';", source)
        self.assertIn(".csf-actions{display:none!important}", source)
        self.assertIn(".top-phone a[href=\"#phone-modal\"]", source)
        self.assertIn("width:min(420px,calc(100vw - 28px))!important", source)
        self.assertIn(
            "@media(max-width:560px){html,body{max-width:100%;overflow-x:hidden}",
            source,
        )
        self.assertIn(
            "#primary-menu{width:100%!important;min-width:0!important;max-width:100%!important;display:flex!important;flex-wrap:wrap}",
            source,
        )
        self.assertIn("['a[href=\"#phone-modal\"]','callback','ЗАКАЗАТЬ ЗВОНОК']", source)
        self.assertIn("['a[href=\"#license-modal\"]','question','ЗАДАТЬ ВОПРОС']", source)
        self.assertIn("['a[href=\"#back-modal\"]','question','ЗАДАТЬ ВОПРОС']", source)
        self.assertIn("if(el.dataset.csfBound==='1')return", source)

        question_form = source.split('data-modal="question"', 1)[1]
        self.assertTrue(
            question_form.index('name="name"')
            < question_form.index('name="phone"')
            < question_form.index('name="question"')
            < question_form.index('name="captcha"')
        )
        self.assertNotIn('name="email"', question_form)

    def test_apreal72_maps_legacy_modal_links_and_hides_fixed_actions(self):
        module = load_module()
        source = module.render_wordpress_plugin("apreal72.ru", "info@apreal72.ru")

        self.assertIn("const CSF_SENDER = 'info@apreal72.ru';", source)
        self.assertIn(".csf-actions{display:none!important}", source)
        self.assertIn("['a[href=\"#phone-modal\"]','callback','ЗАКАЗАТЬ ЗВОНОК']", source)
        self.assertIn("['a[href=\"#license-modal\"]','question','ЗАДАТЬ ВОПРОС']", source)
        self.assertIn("['a[href=\"#back-modal\"]','question','ЗАДАТЬ ВОПРОС']", source)
        self.assertIn("if(el.dataset.csfBound==='1')return", source)
        self.assertIn(
            "@media(max-width:560px){html,body{max-width:100%;overflow-x:hidden}",
            source,
        )
        self.assertIn(
            "#primary-menu{width:100%!important;min-width:0!important;max-width:100%!important;display:flex!important;flex-wrap:wrap}",
            source,
        )

    def test_shopap_places_standard_actions_in_page_flow(self):
        module = load_module()
        script = module.render_static_script("shopap.ru")

        self.assertIn("csf-actions-shop", script)
        self.assertIn("document.querySelector('#content')", script)
        self.assertIn("insertBefore(actions,shopContent.firstChild)", script)
        self.assertIn("position:static", script)
        self.assertIn("grid-template-columns:1fr 1fr", script)

    def test_nousro_omits_standard_actions_by_client_request(self):
        module = load_module()
        source = module.render_wordpress_plugin("nousro.ru", "info@nousro.ru")

        self.assertNotIn('class="csf-actions"', source)
        self.assertNotIn("csf-actions-nousro", source)

    def test_ed_kgd_omits_standard_actions_and_frontend_admin_bar(self):
        module = load_module()
        source = module.render_wordpress_plugin("ed-kgd.ru", "info@ed-kgd.ru")

        self.assertNotIn('class="csf-actions"', source)
        self.assertIn("add_filter('show_admin_bar', '__return_false');", source)
        self.assertIn("remove_action('wp_footer', 'wp_admin_bar_render', 1000);", source)
        self.assertIn("#wpadminbar{display:none!important}", source)

    def test_muc_vrn_removes_fixed_actions_and_promotes_header_callback(self):
        module = load_module()
        source = module.render_wordpress_plugin("muc-vrn.ru", "info@muc-vrn.ru")

        self.assertIn(".csf-actions{display:none!important}", source)
        self.assertIn("csf-muc-header-callback", source)
        self.assertIn("document.querySelector('.fixed-line-right a')", source)
        self.assertIn("document.querySelector('.logotype')", source)
        self.assertIn("header.insertBefore(headerCallback,contacts)", source)
        self.assertIn("document.querySelector('.mob-dop-btns a')", source)
        self.assertIn("mobileCallback.removeAttribute('target')", source)

    def test_component_resists_legacy_hidden_and_chat_styles(self):
        module = load_module()
        wordpress = module.render_wordpress_plugin("example.ru", "info@example.ru")
        static = module.render_static_script("example.ru")

        for source in (wordpress, static):
            self.assertIn(".csf-overlay[hidden],.csf-modal[hidden]", source)
            self.assertIn("display:none!important", source)
            self.assertIn("right:96px", source)
            self.assertIn("html.client-contact-modal-open body > jdiv", source)
            self.assertIn("classList.add('client-contact-modal-open')", source)
            self.assertIn("classList.remove('client-contact-modal-open')", source)
        self.assertIn("document.body.appendChild(root)", wordpress)

    def test_static_script_is_ascii_for_legacy_page_encodings(self):
        module = load_module()
        script = module.render_static_script("example.ru")

        script.encode("ascii")

    def test_apreal_volgograd_retires_legacy_cf7_routes(self):
        module = load_module()
        protected = module.render_wordpress_plugin(
            "apreal-volgograd.ru",
            "vlg-ap@bk.ru",
        )
        ordinary = module.render_wordpress_plugin(
            "example.ru",
            "info@example.ru",
        )

        self.assertIn("csf_block_legacy_cf7", protected)
        self.assertIn("3261, 3317, 3497", protected)
        self.assertIn("wpcf7_spam", protected)
        self.assertIn("WPCF7_ContactForm::get_current()", protected)
        self.assertNotIn("csf_block_legacy_cf7", ordinary)

    def test_build_refuses_excluded_domains(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                module.build_domain(
                    Path(temp_dir),
                    "rectavr.ru",
                    "info@rectavr.ru",
                    "wordpress",
                )


if __name__ == "__main__":
    unittest.main()
