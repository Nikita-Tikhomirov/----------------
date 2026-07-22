import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "changes" / "2026-07-22" / "deploy_nousro_spb_feedback.py"
PLUGIN_PATH = ROOT / "changes" / "2026-07-22" / "nousro-spb-question-fix.php"


def load_module():
    spec = importlib.util.spec_from_file_location("deploy_nousro_spb_feedback", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NousroSpbFeedbackTests(unittest.TestCase):
    def test_question_mail_keeps_regional_and_adds_central_recipient(self):
        module = load_module()
        original = {
            "active": True,
            "recipient": "spb@nousro.ru",
            "subject": "Вопрос с сайта nousro-spb.ru",
        }

        updated = module.with_fallback_recipient(original)

        self.assertEqual("spb@nousro.ru, info@nousro.ru", updated["recipient"])
        self.assertEqual(original["subject"], updated["subject"])
        self.assertEqual("spb@nousro.ru", original["recipient"])

    def test_plugin_moves_response_before_submit_and_hides_chat(self):
        source = PLUGIN_PATH.read_text(encoding="utf-8")

        self.assertIn("nousro-spb-question-open", source)
        self.assertIn("body > jdiv", source)
        self.assertIn("insertBefore(response, submit)", source)
        self.assertIn("wpcf7mailsent", source)
        self.assertIn("#modal1 .wpcf7-response-output", source)
        self.assertIn("setTimeout(function()", source)
        self.assertIn("response.scrollIntoView({block:'center'})", source)


if __name__ == "__main__":
    unittest.main()
