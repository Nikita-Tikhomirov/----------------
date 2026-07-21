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
        self.assertIn("name=\"email\"", source)
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

    def test_static_bundle_uses_domain_recipient(self):
        module = load_module()
        handler = module.render_static_handler("example.ru", "help@example.ru")
        script = module.render_static_script()

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
        self.assertIn("\\u043f\\u043e\\u0434\\u0430\\u0442\\u044c", script)
        self.assertIn("csf-actions-sidebar", script)
        self.assertIn("document.querySelector('#leblok')", script)
        self.assertNotIn("csf-actions-has-legacy-callback", script)

    def test_component_resists_legacy_hidden_and_chat_styles(self):
        module = load_module()
        wordpress = module.render_wordpress_plugin("example.ru", "info@example.ru")
        static = module.render_static_script()

        for source in (wordpress, static):
            self.assertIn(".csf-overlay[hidden],.csf-modal[hidden]", source)
            self.assertIn("display:none!important", source)
            self.assertIn("right:96px", source)
        self.assertIn("document.body.appendChild(root)", wordpress)

    def test_static_script_is_ascii_for_legacy_page_encodings(self):
        module = load_module()
        script = module.render_static_script()

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
