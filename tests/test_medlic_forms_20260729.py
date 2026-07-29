from pathlib import Path


PLUGIN = (
    Path(__file__).resolve().parents[1]
    / "changes"
    / "2026-07-29"
    / "medlic.spb.ru"
    / "client-standard-forms.php"
)


def test_medlic_forms_match_client_contract():
    source = PLUGIN.read_text(encoding="utf-8")

    assert "const CSF_RECIPIENT = 'info@medlic.spb.ru';" in source
    assert '<div class="csf-actions"' not in source
    assert ".csf-actions{" not in source
    assert "html.client-contact-modal-open body > jdiv" in source
    assert "classList.add('client-contact-modal-open')" in source
    assert "classList.remove('client-contact-modal-open')" in source

    callback = source.split('data-modal="callback"', 1)[1].split("</section>", 1)[0]
    question = source.split('data-modal="question"', 1)[1].split("</section>", 1)[0]

    assert callback.index('name="name"') < callback.index('name="phone"')
    assert question.index('name="name"') < question.index('name="phone"')
    assert question.index('name="phone"') < question.index('name="question"')


def test_medlic_mail_handler_keeps_contact_details():
    source = PLUGIN.read_text(encoding="utf-8")

    assert source.count("$name = csf_clean_text('name');") == 2
    assert source.count("$phone = csf_clean_text('phone');") == 2
    assert "if ($phone === '')" in source
    assert "<strong>Имя:</strong>" in source
    assert "<strong>Телефон:</strong>" in source
