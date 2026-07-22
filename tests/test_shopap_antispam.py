import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "changes"
    / "2026-07-22"
    / "deploy_shopap_feedback.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("deploy_shopap_feedback", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ShopapAntispamTests(unittest.TestCase):
    def test_registration_captcha_configuration_is_scoped_to_register(self):
        module = load_module()
        php = module.build_antispam_php("/home/n/nousroc9/shopap.ru/public_html")

        self.assertIn("basic_captcha_status", php)
        self.assertIn("config_captcha_page", php)
        self.assertIn("json_encode(array('register'))", php)
        self.assertNotIn("'review'", php)
        self.assertNotIn("'contact'", php)
        self.assertIn("begin_transaction", php)
        self.assertIn("rollback", php)
        self.assertIn("settings-before.json", php)

    def test_footer_include_gets_a_cache_busting_version(self):
        module = load_module()
        before = b'<script src="/client-standard-forms.js" defer></script>\n'

        after = module.update_footer_include(before)

        expected = f"/client-standard-forms.js?v={module.CACHE_BUSTER}".encode("ascii")
        self.assertIn(expected, after)
        self.assertNotEqual(before, after)


if __name__ == "__main__":
    unittest.main()
