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
        self.assertIn(".header-top .calc-button", otxodi)
        self.assertIn(".header-top .backform", otxodi)
        self.assertIn("csf-actions-mobile", otxodi)
        self.assertIn("insertAdjacentElement('afterend'", otxodi)
        self.assertNotIn(".csf-actions{display:none!important}", ordinary)

    def test_apreal_spb_uses_existing_buttons_with_correct_form_kinds(self):
        module = load_module()
        source = module.render_wordpress_plugin("apreal.spb.ru", "spb@apreal.ru")

        self.assertIn("const CSF_SENDER = 'spb@apreal.ru';", source)
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
