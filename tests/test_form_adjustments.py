from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FormAdjustmentTests(unittest.TestCase):
    def test_elecktro_header_button_opens_form_directly(self):
        theme = (
            ROOT
            / "changes"
            / "2026-07-19"
            / "elecktro.ru"
            / "wp-content"
            / "themes"
            / "yoo_finch_wp"
            / "layouts"
            / "theme.php"
        ).read_text(encoding="utf-8")

        self.assertIn('class="uk-button eModal-1"', theme)
        self.assertNotIn("data-uk-dropdown=\"{mode:'click'}\"", theme)

    def test_elecktro_form_migration_removes_email(self):
        migration = (
            ROOT
            / "changes"
            / "2026-07-19"
            / "elecktro.ru"
            / "apply-form-fix.php"
        ).read_text(encoding="utf-8")

        self.assertNotIn("[email", migration)
        self.assertIn("[text your-name]", migration)
        self.assertIn("[tel* tel-639]", migration)
        self.assertIn("'post_title' => 'ЗАКАЗАТЬ ЗВОНОК'", migration)

    def test_mca_question_text_is_optional_in_markup(self):
        footer = (
            ROOT
            / "changes"
            / "2026-07-19"
            / "mca24.ru"
            / "wp-content"
            / "themes"
            / "mca"
            / "footer.php"
        ).read_text(encoding="utf-8")

        self.assertIn('<textarea name="coment" placeholder="Вопрос"></textarea>', footer)
        self.assertNotIn('<textarea name="coment" required', footer)

    def test_mca_handler_accepts_an_empty_question(self):
        handler = (
            ROOT
            / "changes"
            / "2026-07-19"
            / "mca24.ru"
            / "mail.php"
        ).read_text(encoding="utf-8")

        self.assertNotIn("if ($comment === '')", handler)
        self.assertIn("Вопрос:</strong> {$comment}", handler)


if __name__ == "__main__":
    unittest.main()
