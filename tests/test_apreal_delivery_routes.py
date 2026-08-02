from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.deploy_apreal_delivery_routes import desired_mail_state, route_forms


def test_nousro_spb_routes_match_the_client_site_mailbox():
    forms = route_forms()

    assert forms["callback"]["recipient"] == "spb@nousro.ru"
    assert forms["question"]["recipient"] == "spb@nousro.ru"


def test_delivery_route_change_only_updates_recipient():
    current = {
        "active": True,
        "sender": "nousro-spb.ru <wordpress@nousro-spb.ru>",
        "recipient": "spb@nousro.ru",
        "body": "unchanged",
        "additional_headers": "Reply-To: sender@example.test\nBcc: upreal@bk.ru",
    }

    target = desired_mail_state(current, "spb@nousro.ru")

    assert target == {
        **current,
        "additional_headers": "Reply-To: sender@example.test",
    }
    assert current["recipient"] == "spb@nousro.ru"
