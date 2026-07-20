import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "changes"
    / "2026-07-20"
    / "audit_forms.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("audit_forms", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FormAuditTests(unittest.TestCase):
    def test_detects_complete_standard_form_markup(self):
        module = load_module()
        html = """
        <button>ЗАКАЗАТЬ ЗВОНОК</button>
        <button>ЗАДАТЬ ВОПРОС</button>
        <form>
          <input type="tel" name="phone" required>
          <label>Нажимая на кнопку "Отправить" я даю согласие
          на обработку персональных данных на условиях
          <a href="https://www.apreal.ru/konfedencialnost.html">
          Политики обработки персональных данных</a></label>
        </form>
        <div>Спасибо за Ваше сообщение. Оно успешно отправлено</div>
        """

        result = module.detect_features(html)

        self.assertTrue(result["callback_label"])
        self.assertTrue(result["question_label"])
        self.assertTrue(result["consent"])
        self.assertTrue(result["policy_link"])
        self.assertTrue(result["success_message"])

    def test_detects_legacy_labels_as_gaps(self):
        module = load_module()
        result = module.detect_features(
            "<button>Бесплатная консультация</button>"
            "<button>Расчет стоимости</button>"
        )

        self.assertFalse(result["callback_label"])
        self.assertFalse(result["question_label"])
        self.assertTrue(result["legacy_labels"])


if __name__ == "__main__":
    unittest.main()
