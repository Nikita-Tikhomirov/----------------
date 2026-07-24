import importlib.util
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "changes" / "2026-07-20" / "build_standard_forms.py"
APREAL36 = ROOT / "changes" / "2026-07-23" / "apreal36.ru" / "deploy"


def load_generator():
    spec = importlib.util.spec_from_file_location("build_standard_forms", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClientFeedback20260723Tests(unittest.TestCase):
    def test_public_wordpress_forms_refresh_cached_nonce_and_retry_once(self):
        module = load_generator()
        source = module.render_wordpress_plugin("apreal.spb.ru", "spb@apreal.ru")

        self.assertIn("function csf_refresh_nonce()", source)
        self.assertIn("wp_ajax_nopriv_csf_refresh_nonce", source)
        self.assertIn("refreshNonce().then(function(nonce)", source)
        self.assertIn("if(response.status===403&&attempt===0)", source)
        self.assertIn("const CSF_SENDER = 'wordpress@apreal.spb.ru';", source)

    def test_legacy_phone_forms_use_standard_handler(self):
        module = load_generator()

        for domain, recipient in (
            ("apreal.spb.ru", "spb@apreal.ru"),
            ("license39.ru", "info@license39.ru"),
            ("apreal-nn.ru", "info@apreal-nn.ru"),
        ):
            with self.subTest(domain=domain):
                source = module.render_wordpress_plugin(domain, recipient)
                self.assertIn(
                    'input[name="form-action"][value="phone"]',
                    source,
                )
                self.assertIn("bindLegacyPhoneForms", source)
                self.assertIn("legacyPhoneForm.dataset.csfBound", source)
                self.assertIn("submitStandardPayload(payload,0)", source)
                self.assertIn("csf-inline-result", source)
                self.assertIn("csf-legacy-phone-form", source)
                self.assertIn("grid-template-columns:minmax(0,240px) minmax(0,240px) max-content", source)
                self.assertIn(
                    ".csf-legacy-phone-form>.inp1,.csf-legacy-phone-form>.inp2,.csf-legacy-phone-form>.inp3{position:static!important",
                    source,
                )
                self.assertIn(
                    ".csf-legacy-phone-form>.inp3 input{position:static!important",
                    source,
                )
                self.assertIn(
                    "box-sizing:border-box!important;margin:0!important",
                    source,
                )

    def test_apreal_nn_legacy_fields_match_apreal_reference_dimensions(self):
        module = load_generator()
        source = module.render_wordpress_plugin("apreal-nn.ru", "info@apreal-nn.ru")

        self.assertIn(
            '.infographic input[name="phone-name"],'
            '.infographic input[name="phone-phone"]',
            source,
        )
        self.assertIn("width:240px!important", source)
        self.assertIn("height:42px!important", source)
        self.assertIn("font-size:16px!important", source)

    def test_shopap_question_form_keeps_question_and_visible_captcha(self):
        module = load_generator()
        script = module.render_static_script("shopap.ru")
        script = re.sub(
            r"\\u([0-9a-fA-F]{4})",
            lambda match: chr(int(match.group(1), 16)),
            script,
        )
        handler = module.render_static_handler("shopap.ru", "info@shopap.ru")
        question = script.split('data-modal="question"', 1)[1]

        self.assertIn('name="name"', question)
        self.assertIn('name="phone"', question)
        self.assertIn('name="question"', question)
        self.assertIn('name="captcha" required', question)
        self.assertIn('Введите цифрами: пять', question)
        self.assertNotIn('name="email"', question)

        question_handler = handler.split(
            "} elseif ($kind === 'question') {",
            1,
        )[1].split("} else {", 1)[0]
        self.assertIn("$_POST['name']", question_handler)
        self.assertIn("$_POST['phone']", question_handler)
        self.assertIn("$_POST['question']", question_handler)
        self.assertNotIn("$_POST['email']", question_handler)

    def test_nousro_nn_replaces_old_request_modal_and_hides_fixed_actions(self):
        module = load_generator()
        source = module.render_wordpress_plugin(
            "nousro-nn.ru",
            "info@nousro-nn.ru",
        )

        self.assertIn(".csf-actions{display:none!important}", source)
        self.assertIn("['#mail-us','callback','ОТПРАВИТЬ ЗАЯВКУ']", source)
        self.assertIn(
            '<h2 id="csf-callback-title">ОСТАВИТЬ ЗАЯВКУ</h2>',
            source,
        )
        self.assertIn("html.client-contact-modal-open body > jdiv", source)

    def test_apreal36_popup_fits_mobile_viewport(self):
        footer = (
            APREAL36
            / "wp-content"
            / "themes"
            / "basic"
            / "footer.php"
        ).read_text(encoding="utf-8")
        self.assertIn("width: min(600px, calc(100vw - 30px));", footer)
        self.assertIn("max-height: calc(100vh - 30px);", footer)
        self.assertIn("box-sizing: border-box;", footer)

    def test_apreal36_question_form_and_legacy_buttons_use_phone_form(self):
        footer = (
            APREAL36
            / "wp-content"
            / "themes"
            / "basic"
            / "footer.php"
        ).read_text(encoding="utf-8")
        handler = (APREAL36 / "mail.php").read_text(encoding="utf-8")

        question = footer.split('data-form="question"', 1)[1].split("</form>", 1)[0]
        self.assertIn('name="name"', question)
        self.assertIn('name="phone"', question)
        self.assertIn('name="coment"', question)
        self.assertNotIn('name="email"', question)
        self.assertIn("bindQuestionTriggers", footer)
        self.assertIn('[href="#modal-full"]', footer)
        self.assertIn("event.stopImmediatePropagation()", footer)

        question_handler = handler.split(
            "} elseif ($form_id === 'question') {",
            1,
        )[1].split("} else {", 1)[0]
        self.assertIn("$_POST['phone']", question_handler)
        self.assertNotIn("$_POST['email']", question_handler)


if __name__ == "__main__":
    unittest.main()
