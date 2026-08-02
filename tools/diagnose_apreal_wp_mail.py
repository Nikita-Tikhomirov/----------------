#!/usr/bin/env python3
"""Run a marked WordPress mail probe and print the exact wp_mail failure data."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import re

try:
    from tools.deploy_apreal_standard_family import connect, run_remote, wp_command
except ModuleNotFoundError:
    from deploy_apreal_standard_family import connect, run_remote, wp_command


ROOT = Path(__file__).resolve().parents[1]


def validate_domain(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9.-]+", value):
        raise argparse.ArgumentTypeError("invalid domain")
    return value


def validate_sender(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9._%+-]+@[a-z0-9.-]+", value):
        raise argparse.ArgumentTypeError("invalid sender")
    return value


def build_probe(sender: str, marker: str) -> str:
    sender_json = json.dumps(sender)
    marker_json = json.dumps(marker)
    return f"""
$error = null;
$transport = null;
add_action('wp_mail_failed', function($value) use (&$error) {{
    $error = array(
        'message' => $value->get_error_message(),
        'data' => $value->get_error_data(),
    );
}});
add_action('phpmailer_init', function($mailer) use (&$transport) {{
    $transport = array(
        'mailer' => $mailer->Mailer,
        'host' => $mailer->Host,
        'username' => $mailer->Username,
        'from' => $mailer->From,
        'from_name' => $mailer->FromName,
        'reply_to' => $mailer->getReplyToAddresses(),
        'sender_before' => $mailer->Sender,
    );
    $mailer->Sender = {sender_json};
}}, 999);
$result = wp_mail(
    'upreal@bk.ru',
    {marker_json},
    'Technical diagnostic, no reply required',
    array(
        'From: AP-Real QA <' . {sender_json} . '>',
        'Reply-To: ' . {sender_json}
    )
);
echo wp_json_encode(
    array('result' => $result, 'transport' => $transport, 'error' => $error),
    JSON_UNESCAPED_UNICODE
);
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", type=validate_domain)
    parser.add_argument("sender", type=validate_sender)
    parser.add_argument("marker")
    parser.add_argument("--credentials", type=Path, default=ROOT / "Упавшая сессия.txt")
    parser.add_argument("--host", default="nousroc9.beget.tech")
    parser.add_argument("--user", default="nousroc9")
    args = parser.parse_args()

    ssh = connect(args)
    try:
        payload = base64.b64encode(build_probe(args.sender, args.marker).encode()).decode()
        output = run_remote(
            ssh,
            wp_command(args.domain, "eval", f'eval(base64_decode("{payload}"));'),
        )
        print(output)
    finally:
        ssh.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
