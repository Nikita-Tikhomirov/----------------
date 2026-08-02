import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.deploy_apreal_cf7_recipient_normalization import (
    RECIPIENT_UPDATES,
    build_exact_mail_update_eval,
    decode_mail_payload,
    desired_mail_state,
    encode_mail_payload,
)
import tools.deploy_apreal_cf7_recipient_normalization as normalization


def test_recipient_update_matrix_is_explicit_and_complete():
    assert len(RECIPIENT_UPDATES) == 16
    assert {
        (item.domain, item.form_id, item.current_recipient, item.target_recipient)
        for item in RECIPIENT_UPDATES
    } == {
        ("apreal.ru", 6945, "upreal@bk.ru", "info@apreal.ru"),
        ("apreal.ru", 6947, "upreal@bk.ru", "info@apreal.ru"),
        ("apreal.ru", 6959, "upreal@bk.ru", "info@apreal.ru"),
        ("docp.ru", 3260, "upreal@bk.ru", "info@docp.ru"),
        ("docp.ru", 3261, "upreal@bk.ru", "info@docp.ru"),
        ("docp.ru", 3317, "upreal@bk.ru", "info@docp.ru"),
        ("docp.ru", 3497, "upreal@bk.ru", "info@docp.ru"),
        ("apreal.spb.ru", 22, "upreall@yandex.ru", "spb@apreal.ru"),
        ("apreal.spb.ru", 1960, "upreall@yandex.ru", "spb@apreal.ru"),
        ("mchs78.ru", 63, "admin@admin.com", "info@mchs78.ru"),
        ("nousro-spb.ru", 2006, "info@nousro.ru", "spb@nousro.ru"),
        ("nousro-spb.ru", 2400, "info@nousro.ru", "spb@nousro.ru"),
        ("nousro-spb.ru", 2434, "nousro-muc@yandex.ru", "spb@nousro.ru"),
        ("ed-kgd.ru", 212, "info@nousro.ru", "info@ed-kgd.ru"),
        ("nousro-nn.ru", 47, "info@nousro.ru", "info@nousro-nn.ru"),
        ("nousro-nn.ru", 3307, "info@nousro.ru", "info@nousro-nn.ru"),
    }


def test_recipient_targets_match_the_client_scope():
    scope = json.loads(
        (ROOT / "changes" / "2026-07-20" / "form-audit-scope.json").read_text(
            encoding="utf-8"
        )
    )
    recipients = {item["domain"]: item["recipient"] for item in scope["sites"]}

    for item in RECIPIENT_UPDATES:
        assert item.target_recipient == recipients[item.domain]


def test_desired_mail_state_changes_recipient_and_removes_central_bcc():
    current = {
        "active": True,
        "sender": "Website <wordpress@example.test>",
        "recipient": "old@example.test",
        "subject": "Keep this",
        "body": "Keep this too",
        "additional_headers": (
            "Reply-To: reply@example.test\r\n"
            "Bcc: Other <other@example.test>, upreal@bk.ru\r\n"
        ),
        "use_html": False,
        "exclude_blank": False,
        "attachments": "",
    }

    target = desired_mail_state(
        current,
        expected_recipient="old@example.test",
        target_recipient="new@example.test",
    )

    assert target == {
        **current,
        "recipient": "new@example.test",
        "additional_headers": (
            "Reply-To: reply@example.test\r\n"
            "Bcc: Other <other@example.test>\r\n"
        ),
    }
    assert current["recipient"] == "old@example.test"
    assert "upreal@bk.ru" in current["additional_headers"]


def test_desired_mail_state_rejects_an_unexpected_live_recipient():
    with pytest.raises(RuntimeError, match="Live recipient changed after audit"):
        desired_mail_state(
            {"recipient": "someone-else@example.test"},
            expected_recipient="old@example.test",
            target_recipient="new@example.test",
        )


def test_exact_mail_update_preserves_json_value_types():
    mail = {
        "active": True,
        "recipient": "info@example.test",
        "use_html": False,
        "exclude_blank": False,
    }

    encoded = encode_mail_payload(mail)

    assert decode_mail_payload(encoded) == mail
    php = build_exact_mail_update_eval(3260, mail)
    assert encoded in php
    assert "COUNT(*)" in php
    assert "maybe_serialize" in php
    assert "_mail" in php


def test_rollback_restores_and_verifies_every_form(monkeypatch):
    item = normalization.RecipientUpdate(
        "example.test",
        "/srv/example",
        42,
        "Contact",
        "old@example.test",
        "new@example.test",
    )
    baseline = {
        "title": "Contact",
        "status": "publish",
        "mail": {"recipient": "old@example.test"},
    }
    live = {**baseline, "mail": {"recipient": "new@example.test"}}
    states = iter((live, baseline))
    restored = []

    monkeypatch.setattr(normalization, "get_form_state", lambda ssh, update: next(states))
    monkeypatch.setattr(
        normalization,
        "set_mail_exact",
        lambda ssh, update, mail: restored.append(mail),
    )

    normalization.rollback_to_snapshot(
        object(),
        {"forms": {normalization.form_key(item): baseline}},
        (item,),
    )

    assert restored == [baseline["mail"]]


def test_rollback_fails_when_restored_state_does_not_match_snapshot(monkeypatch):
    item = normalization.RecipientUpdate(
        "example.test",
        "/srv/example",
        42,
        "Contact",
        "old@example.test",
        "new@example.test",
    )
    baseline = {
        "title": "Contact",
        "status": "publish",
        "mail": {"recipient": "old@example.test"},
    }
    live = {**baseline, "mail": {"recipient": "new@example.test"}}

    monkeypatch.setattr(normalization, "get_form_state", lambda ssh, update: live)
    monkeypatch.setattr(normalization, "set_mail_exact", lambda ssh, update, mail: None)

    with pytest.raises(RuntimeError, match="Rollback verification failed"):
        normalization.rollback_to_snapshot(
            object(),
            {"forms": {normalization.form_key(item): baseline}},
            (item,),
        )
