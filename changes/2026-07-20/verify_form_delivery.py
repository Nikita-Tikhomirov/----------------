#!/usr/bin/env python3
"""Exercise every newly installed form handler and record its mail result."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import urljoin

import requests


BASE = Path(__file__).resolve().parent
OUTPUT = BASE / "form-delivery-results.json"
GENERATOR = BASE / "build_standard_forms.py"
MARKER = "csf-delivery-check=2026-07-20"


def load_generator():
    spec = importlib.util.spec_from_file_location("form_generator", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_wordpress_contract(html: str) -> tuple[str, str]:
    root = re.search(
        r'class="csf-root"\s+data-endpoint="([^"]+)"',
        html,
    )
    nonce = re.search(
        r'name="nonce"\s+value="([^"]+)"',
        html,
    )
    if not root or not nonce:
        raise RuntimeError("Standard WordPress form contract is missing")
    return root.group(1).replace("&amp;", "&"), nonce.group(1)


def decode_json(response: requests.Response) -> dict:
    try:
        return response.json()
    except ValueError as error:
        excerpt = response.text[:300].replace("\n", " ")
        raise RuntimeError(f"Non-JSON response: {excerpt}") from error


def post_form(
    session: requests.Session,
    endpoint: str,
    data: dict,
) -> tuple[int, dict]:
    response = session.post(
        endpoint,
        data=data,
        timeout=35,
        headers={"Referer": data["page"]},
    )
    return response.status_code, decode_json(response)


def test_domain(
    domain: str,
    platform: str,
    send_callback: bool,
    send_question: bool,
) -> dict:
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124 Safari/537.36"
    )
    page_url = f"https://{domain}/?{MARKER}"
    page = session.get(page_url, timeout=35)
    page.raise_for_status()

    if platform == "wordpress":
        endpoint, nonce = extract_wordpress_contract(page.text)
        endpoint = urljoin(page.url, endpoint)
        common = {"action": "csf_send_form", "nonce": nonce}
    else:
        endpoint = urljoin(page.url, "/client-standard-mail.php")
        common = {}

    invalid_data = {
        **common,
        "kind": "callback",
        "page": page.url,
        "website": "",
        "phone": "+7 999 000-20-07",
        "captcha": "4",
    }
    invalid_status, invalid_payload = post_form(
        session,
        endpoint,
        invalid_data,
    )
    invalid_ok = (
        invalid_status == 400
        and invalid_payload.get("success") is False
    )

    valid_status = None
    valid_payload = None
    valid_ok = None
    if send_callback:
        valid_data = dict(invalid_data)
        valid_data["captcha"] = "5"
        valid_status, valid_payload = post_form(
            session,
            endpoint,
            valid_data,
        )
        valid_ok = (
            valid_status == 200
            and valid_payload.get("success") is True
        )

    invalid_question_data = {
        **common,
        "kind": "question",
        "page": page.url,
        "website": "",
        "email": "not-an-email",
        "question": "Техническая проверка формы",
        "captcha": "5",
    }
    question_invalid_status, question_invalid_payload = post_form(
        session,
        endpoint,
        invalid_question_data,
    )
    question_invalid_ok = (
        question_invalid_status == 400
        and question_invalid_payload.get("success") is False
    )

    question_status = None
    question_payload = None
    question_ok = None
    if send_question:
        valid_question_data = dict(invalid_question_data)
        valid_question_data["email"] = "stithc92@gmail.com"
        question_status, question_payload = post_form(
            session,
            endpoint,
            valid_question_data,
        )
        question_ok = (
            question_status == 200
            and question_payload.get("success") is True
        )

    return {
        "domain": domain,
        "platform": platform,
        "page_status": page.status_code,
        "endpoint": endpoint,
        "invalid_captcha": {
            "status": invalid_status,
            "accepted": invalid_ok,
            "payload": invalid_payload,
        },
        "valid_callback": {
            "sent": send_callback,
            "status": valid_status,
            "accepted": valid_ok,
            "payload": valid_payload,
        },
        "invalid_question_email": {
            "status": question_invalid_status,
            "accepted": question_invalid_ok,
            "payload": question_invalid_payload,
        },
        "valid_question": {
            "sent": send_question,
            "status": question_status,
            "accepted": question_ok,
            "payload": question_payload,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send one marked callback email through every handler.",
    )
    parser.add_argument(
        "--question-samples",
        action="store_true",
        help="Send question forms on one WordPress and one static site.",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    generator = load_generator()
    sites = [
        *((domain, "wordpress") for domain in generator.WORDPRESS_SITES),
        *((domain, "static") for domain in generator.STATIC_SITES),
    ]

    results = []
    for index, (domain, platform) in enumerate(sites, start=1):
        try:
            send_question = (
                args.question_samples
                and domain in {"docp.ru", "fste.ru"}
            )
            result = test_domain(
                domain,
                platform,
                args.send,
                send_question,
            )
            result["error"] = ""
        except Exception as error:
            result = {
                "domain": domain,
                "platform": platform,
                "error": str(error),
            }
        results.append(result)
        print(
            f"{index}/{len(sites)} {domain} "
            f"{'ERROR' if result['error'] else 'OK'}",
            flush=True,
        )

    args.output.write_text(
        json.dumps(
            {
                "marker": MARKER,
                "actual_mail_requested": args.send,
                "question_samples_requested": args.question_samples,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    failed = [
        item["domain"]
        for item in results
        if item.get("error")
        or not item.get("invalid_captcha", {}).get("accepted")
        or not item.get("invalid_question_email", {}).get("accepted")
        or (
            args.send
            and not item.get("valid_callback", {}).get("accepted")
        )
        or (
            args.question_samples
            and item["domain"] in {"docp.ru", "fste.ru"}
            and not item.get("valid_question", {}).get("accepted")
        )
    ]
    print(
        json.dumps(
            {"total": len(results), "failed": failed},
            ensure_ascii=True,
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
