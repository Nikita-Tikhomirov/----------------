from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.deploy_apreal_delivery_routes import desired_mail_state, route_forms


def test_nousro_spb_routes_preserve_domain_mailboxes_and_add_central_copy():
    forms = route_forms()

    assert forms["callback"]["recipient"] == "spb@nousro.ru, upreal@bk.ru"
    assert forms["question"]["recipient"] == (
        "spb@nousro.ru, info@nousro.ru, upreal@bk.ru"
    )


def test_delivery_route_change_only_updates_recipient():
    current = {
        "active": True,
        "sender": "nousro-spb.ru <wordpress@nousro-spb.ru>",
        "recipient": "spb@nousro.ru",
        "body": "unchanged",
    }

    target = desired_mail_state(current, "spb@nousro.ru, upreal@bk.ru")

    assert target == {
        **current,
        "recipient": "spb@nousro.ru, upreal@bk.ru",
    }
    assert current["recipient"] == "spb@nousro.ru"
