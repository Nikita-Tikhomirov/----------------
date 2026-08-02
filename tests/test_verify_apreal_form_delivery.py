from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module():
    import importlib.util

    path = ROOT / "tools" / "verify_apreal_form_delivery.py"
    spec = importlib.util.spec_from_file_location("verify_apreal_form_delivery", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scope_is_exactly_30_included_sites():
    module = load_module()

    assert len(module.SITE_CONTRACTS) == 30
    assert set(module.SITE_CONTRACTS) == set(module.STANDARD_SITES) | set(
        module.CUSTOM_SITES
    )
    assert not set(module.SITE_CONTRACTS) & module.EXCLUDED_SITES


@pytest.mark.parametrize("kind", ["callback", "question"])
def test_standard_payload_has_marker_phone_captcha_and_no_email(kind):
    module = load_module()

    payload = module.standard_payload(
        kind=kind,
        marker="APREAL-QA-20260802-example-" + kind,
        page="https://example.ru/",
        common={"action": "csf_send_form", "nonce": "abc"},
    )

    assert payload["kind"] == kind
    assert payload["captcha"] == "5"
    assert payload["phone"] == module.TEST_PHONE
    assert payload["name"].startswith("Техническая проверка")
    assert "APREAL-QA-20260802-example-" in payload["name"]
    assert "email" not in payload
    assert ("question" in payload) is (kind == "question")


def test_custom_php_payload_uses_deployed_contract():
    module = load_module()

    payload = module.custom_php_payload(
        kind="question",
        marker="APREAL-QA-20260802-mca24-question",
        page="https://mca24.ru/",
    )

    assert payload["formid"] == "question"
    assert payload["captcha"] == "5"
    assert payload["phone"] == module.TEST_PHONE
    assert payload["coment"] == "APREAL-QA-20260802-mca24-question"
    assert "email" not in payload


def test_cf7_payload_preserves_hidden_quiz_token():
    module = load_module()
    html = """
    <form class="wpcf7-form">
      <input type="hidden" name="_wpcf7" value="6740">
      <input type="hidden" name="_wpcf7_unit_tag" value="wpcf7-f6740-o2">
      <input type="hidden" name="_wpcf7_quiz_answer_callback-quiz" value="hash">
      <input type="text" name="f-name">
      <input type="tel" name="f-phone">
      <input type="text" name="callback-quiz">
    </form>
    """

    endpoint, payload = module.cf7_payload(
        domain="apreal.ru",
        html=html,
        form_id=6740,
        kind="callback",
        marker="APREAL-QA-20260802-apreal-callback",
    )

    assert endpoint.endswith("/contact-forms/6740/feedback")
    assert payload["_wpcf7_quiz_answer_callback-quiz"] == "hash"
    assert payload["callback-quiz"] == "5"
    assert payload["f-phone"] == module.TEST_PHONE
    assert payload["f-name"].endswith("APREAL-QA-20260802-apreal-callback")


def test_http_acceptance_alone_is_not_delivery_proof():
    module = load_module()

    result = module.delivery_summary(
        submissions=[
            {"domain": "example.ru", "kind": "callback", "accepted": True},
            {"domain": "example.ru", "kind": "question", "accepted": True},
        ],
        receipts=[],
    )

    assert result["accepted"] == 2
    assert result["delivered"] == 0
    assert result["complete"] is False


def test_beget_cookie_challenge_is_detected():
    module = load_module()

    assert module.is_beget_cookie_challenge(
        "<script>document.cookie='beget=begetok';location.reload();</script>"
    )
    assert not module.is_beget_cookie_challenge('{"status":"mail_sent"}')


def test_medtex_question_requires_rate_limit_pause():
    module = load_module()

    assert module.submission_pause("medtex39.ru", "question") == 31
    assert module.submission_pause("medtex39.ru", "callback") == 0
    assert module.submission_pause("docp.ru", "question") == 0


def test_retry_replaces_failed_checkpoint_entry():
    module = load_module()
    submissions = [
        {"domain": "apreal.ru", "kind": "callback", "accepted": False},
    ]

    module.upsert_submission(
        submissions,
        {"domain": "apreal.ru", "kind": "callback", "accepted": True},
    )

    assert submissions == [
        {"domain": "apreal.ru", "kind": "callback", "accepted": True},
    ]


def test_cf7_request_is_multipart():
    module = load_module()

    kwargs = module.request_payload("cf7", {"field": "value"})

    assert "data" not in kwargs
    assert kwargs["files"] == {"field": (None, "value")}
    assert module.request_payload("wordpress", {"field": "value"}) == {
        "data": {"field": "value"}
    }
