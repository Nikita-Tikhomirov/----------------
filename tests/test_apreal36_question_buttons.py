from pathlib import Path
import unittest


THEME_DIR = (
    Path(__file__).resolve().parents[1]
    / "changes"
    / "2026-07-22"
    / "apreal36.ru"
    / "deploy"
    / "wp-content"
    / "themes"
    / "basic"
)


class Apreal36QuestionButtonTests(unittest.TestCase):
    def test_generated_content_buttons_open_question_form(self):
        footer = (THEME_DIR / "footer.php").read_text(encoding="utf-8")

        replacement = footer.split(
            "const newButton = document.createElement('div');",
            1,
        )[1].split("button.replaceWith(newButton);", 1)[0]
        self.assertIn("'open-question'", replacement)
        self.assertIn("span.textContent = 'ЗАДАТЬ ВОПРОС';", replacement)
        self.assertNotIn("'open-callback'", replacement)

    def test_sidebar_buttons_open_question_form(self):
        for template_name in ("front-page.php", "content-page.php"):
            source = (THEME_DIR / template_name).read_text(encoding="utf-8")
            self.assertIn("open-question", source)
            self.assertIn("Задать вопрос", source)
            self.assertNotIn("open-callback", source)

    def test_callback_and_question_handlers_are_both_available(self):
        footer = (THEME_DIR / "footer.php").read_text(encoding="utf-8")

        self.assertIn("document.querySelectorAll('.open-callback')", footer)
        self.assertIn("openPopup('popup-callback')", footer)
        self.assertIn("document.querySelectorAll('.open-question')", footer)
        self.assertIn("openPopup('popup-question')", footer)

    def test_chat_is_hidden_only_while_a_contact_popup_is_open(self):
        footer = (THEME_DIR / "footer.php").read_text(encoding="utf-8")

        self.assertIn("document.documentElement.classList.add('unipop-open')", footer)
        self.assertIn("document.documentElement.classList.remove('unipop-open')", footer)
        self.assertIn("html.unipop-open body > jdiv", footer)


if __name__ == "__main__":
    unittest.main()
