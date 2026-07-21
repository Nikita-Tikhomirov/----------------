from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SITES = ("mhsl.ru", "med-license.ru")


@pytest.mark.parametrize("domain", SITES)
def test_question_form_uses_question_phone_name_order(domain: str) -> None:
    footer = (
        ROOT
        / "changes"
        / "2026-07-19"
        / domain
        / "wp-content"
        / "themes"
        / "license-center"
        / "footer.php"
    ).read_text(encoding="utf-8")
    block = footer.split('data-form="question"', 1)[1].split("</form>", 1)[0]

    question = block.index('name="coment"')
    phone = block.index('name="phone"')
    name = block.index('name="name"')

    assert question < phone < name
    assert '<input type="tel" name="phone" required' in block
    assert '<input type="text" name="name" placeholder="Имя">' in block
    assert 'name="email"' not in block
    assert "z-index: 2147483600" in footer
    assert "z-index: 2147483601" in footer


@pytest.mark.parametrize("domain", SITES)
def test_question_handler_requires_phone_and_keeps_other_fields_optional(
    domain: str,
) -> None:
    handler = (
        ROOT / "changes" / "2026-07-19" / domain / "mail.php"
    ).read_text(encoding="utf-8")

    question_branch = handler.split("elseif ($form_id === 'question')", 1)[1]

    assert "$_POST['phone']" in question_branch
    assert "$_POST['name']" in question_branch
    assert "$_POST['coment']" in question_branch
    assert "if ($phone === '')" in question_branch
    assert "Введите телефон." in question_branch
    assert "sanitize_email" not in question_branch
    assert "<strong>Телефон:</strong>" in question_branch
    assert "<strong>Имя:</strong>" in question_branch
    assert "<strong>Вопрос:</strong>" in question_branch
