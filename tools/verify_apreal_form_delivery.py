#!/usr/bin/env python3
"""Submit marked AP-Real form checks and keep delivery proof separate."""

from __future__ import annotations

import argparse
from datetime import datetime
import importlib.util
import json
from pathlib import Path
import re
import time
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "changes" / "2026-07-20" / "build_standard_forms.py"
DEFAULT_OUTPUT = ROOT / "output" / "ap-real-form-delivery-2026-08-02.json"
SUCCESS = "Спасибо за Ваше сообщение. Оно успешно отправлено"
TEST_PHONE = "+7 999 000-82-02"
TEST_NAME = "Техническая проверка, отвечать не нужно"

EXCLUDED_SITES = {
    "rectavr.ru",
    "fstek.spb.ru",
    "lic-k.ru",
    "apreal-samara.ru",
    "ed-krd.ru",
}

CUSTOM_PHP_SITES = {
    "mca24.ru",
    "fsa-lab.ru",
    "med-license.ru",
    "mhsl.ru",
    "apreal36.ru",
}

CF7_SITES = {
    "apreal.ru": {
        "callback": {"id": 6740, "name": "f-name", "phone": "f-phone", "quiz": "callback-quiz"},
        "question": {"id": 4399, "name": "f-name", "phone": "f-phone", "question": "f-text", "quiz": "question-quiz"},
    },
    "nousro-spb.ru": {
        "callback": {"id": 2438, "name": "callback-name", "phone": "callback-phone", "quiz": "callback-quiz"},
        "question": {"id": 2005, "name": "question-name", "phone": "question-phone", "question": "question-message", "quiz": "question-quiz"},
    },
}


def _load_generator():
    spec = importlib.util.spec_from_file_location("apreal_standard_forms", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_generator = _load_generator()
STANDARD_SITES = {
    **{domain: "wordpress" for domain in _generator.WORDPRESS_SITES},
    **{domain: "static" for domain in _generator.STATIC_SITES},
}
CUSTOM_SITES = CUSTOM_PHP_SITES | set(CF7_SITES)
SITE_CONTRACTS = {
    **{domain: {"type": platform} for domain, platform in STANDARD_SITES.items()},
    **{domain: {"type": "custom_php"} for domain in CUSTOM_PHP_SITES},
    **{domain: {"type": "cf7"} for domain in CF7_SITES},
}


def extract_wordpress_contract(html: str) -> tuple[str, str]:
    root = re.search(r'class="csf-root"\s+data-endpoint="([^"]+)"', html)
    nonce = re.search(r'name="nonce"\s+value="([^"]+)"', html)
    if not root or not nonce:
        raise RuntimeError("standard WordPress form contract is missing")
    return root.group(1).replace("&amp;", "&"), nonce.group(1)


def marked_name(marker: str) -> str:
    return f"{TEST_NAME} - {marker}"


def standard_payload(kind: str, marker: str, page: str, common: dict[str, str]) -> dict[str, str]:
    payload = {
        **common,
        "kind": kind,
        "page": page,
        "website": "",
        "name": marked_name(marker),
        "phone": TEST_PHONE,
        "captcha": "5",
    }
    if kind == "question":
        payload["question"] = marker
    return payload


def custom_php_payload(kind: str, marker: str, page: str) -> dict[str, str]:
    payload = {
        "formid": kind,
        "page": page,
        "name": marked_name(marker),
        "phone": TEST_PHONE,
        "captcha": "5",
    }
    if kind == "question":
        payload["coment"] = marker
    return payload


def cf7_payload(domain: str, html: str, form_id: int, kind: str, marker: str) -> tuple[str, dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    form = soup.select_one(f'form:has(input[name="_wpcf7"][value="{form_id}"])')
    if form is None:
        raise RuntimeError(f"CF7 form {form_id} is missing on {domain}")
    payload = {
        field.get("name"): field.get("value", "")
        for field in form.select('input[type="hidden"][name]')
    }
    definition = CF7_SITES[domain][kind]
    payload[definition["name"]] = marked_name(marker)
    payload[definition["phone"]] = TEST_PHONE
    payload[definition["quiz"]] = "5"
    if "question" in definition:
        payload[definition["question"]] = marker
    endpoint = f"https://{domain}/wp-json/contact-form-7/v1/contact-forms/{form_id}/feedback"
    return endpoint, payload


def decode_json(response: requests.Response) -> dict[str, Any]:
    try:
        return response.json()
    except ValueError as error:
        excerpt = response.text[:300].replace("\n", " ")
        raise RuntimeError(f"non-JSON response: {excerpt}") from error


def is_beget_cookie_challenge(text: str) -> bool:
    return "document.cookie='beget=begetok'" in text


def post_with_beget_retry(
    session: requests.Session,
    endpoint: str,
    data: dict[str, str],
    page_url: str,
    contract_type: str,
) -> requests.Response:
    payload = request_payload(contract_type, data)
    response = session.post(
        endpoint,
        **payload,
        timeout=45,
        headers={"Referer": page_url},
    )
    if is_beget_cookie_challenge(response.text):
        session.cookies.set("beget", "begetok", domain=new_domain(endpoint), path="/")
        response = session.post(
            endpoint,
            **payload,
            timeout=45,
            headers={"Referer": page_url},
        )
    return response


def request_payload(contract_type: str, data: dict[str, str]) -> dict[str, Any]:
    if contract_type == "cf7":
        return {"files": {name: (None, value) for name, value in data.items()}}
    return {"data": data}


def new_domain(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).hostname or ""


def submission_pause(domain: str, kind: str) -> int:
    return 31 if domain == "medtex39.ru" and kind == "question" else 0


def upsert_submission(submissions: list[dict[str, Any]], result: dict[str, Any]) -> None:
    key = (result["domain"], result["kind"])
    for index, existing in enumerate(submissions):
        if (existing["domain"], existing["kind"]) == key:
            submissions[index] = result
            return
    submissions.append(result)


def is_accepted(contract_type: str, response: requests.Response, payload: dict[str, Any]) -> bool:
    if contract_type == "cf7":
        return response.status_code == 200 and payload.get("status") == "mail_sent"
    if contract_type == "wordpress":
        return response.status_code == 200 and payload.get("success") is True
    return response.status_code == 200 and payload.get("success") is True


def _session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/124 Safari/537.36"
    )
    return session


def submit_one(domain: str, kind: str, marker: str) -> dict[str, Any]:
    contract_type = SITE_CONTRACTS[domain]["type"]
    session = _session()
    page_url = f"https://{domain}/?apreal_delivery_qa={marker}"
    page = session.get(page_url, timeout=40)
    page.raise_for_status()

    if contract_type == "wordpress":
        endpoint, nonce = extract_wordpress_contract(page.text)
        endpoint = urljoin(page.url, endpoint)
        data = standard_payload(kind, marker, page.url, {"action": "csf_send_form", "nonce": nonce})
    elif contract_type == "static":
        endpoint = urljoin(page.url, "/client-standard-mail.php")
        if domain == "medtex39.ru":
            challenge = session.get(f"{endpoint}?challenge=1", timeout=40)
            challenge.raise_for_status()
            token = decode_json(challenge).get("token", "")
            time.sleep(2.2)
            common = {"form_token": token}
        else:
            common = {}
        data = standard_payload(kind, marker, page.url, common)
    elif contract_type == "custom_php":
        endpoint = urljoin(page.url, "/mail.php")
        data = custom_php_payload(kind, marker, page.url)
    else:
        definition = CF7_SITES[domain][kind]
        endpoint, data = cf7_payload(domain, page.text, definition["id"], kind, marker)

    response = post_with_beget_retry(session, endpoint, data, page.url, contract_type)
    payload = decode_json(response)
    return {
        "domain": domain,
        "kind": kind,
        "marker": marker,
        "contract": contract_type,
        "page_status": page.status_code,
        "endpoint": endpoint,
        "status": response.status_code,
        "accepted": is_accepted(contract_type, response, payload),
        "response": payload,
        "submitted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def delivery_summary(submissions: list[dict[str, Any]], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    receipt_markers = {item["marker"] for item in receipts if item.get("found")}
    accepted = sum(bool(item.get("accepted")) for item in submissions)
    delivered = sum(item.get("marker") in receipt_markers for item in submissions)
    total = len(submissions)
    return {
        "total": total,
        "accepted": accepted,
        "delivered": delivered,
        "complete": total > 0 and accepted == total and delivered == total,
    }


def _load_checkpoint(path: Path, marker_prefix: str) -> dict[str, Any]:
    if not path.exists():
        return {"marker_prefix": marker_prefix, "submissions": [], "receipts": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("marker_prefix") != marker_prefix:
        raise RuntimeError("checkpoint marker differs from --marker-prefix")
    return data


def _write_checkpoint(path: Path, data: dict[str, Any]) -> None:
    data["summary"] = delivery_summary(data["submissions"], data.get("receipts", []))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submit", action="store_true", help="Perform real marked submissions.")
    parser.add_argument("--marker-prefix", default="APREAL-QA-20260802")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--domains", nargs="*", choices=sorted(SITE_CONTRACTS))
    args = parser.parse_args()
    domains = args.domains or sorted(SITE_CONTRACTS)
    checkpoint = _load_checkpoint(args.output, args.marker_prefix)
    completed = {
        (item["domain"], item["kind"])
        for item in checkpoint["submissions"]
        if item.get("accepted")
    }

    if not args.submit:
        print(json.dumps({"domains": domains, "forms": len(domains) * 2}, ensure_ascii=False))
        return 0

    failed = []
    for domain in domains:
        for kind in ("callback", "question"):
            if (domain, kind) in completed:
                continue
            pause = submission_pause(domain, kind)
            if pause:
                time.sleep(pause)
            marker = f"{args.marker_prefix}-{domain}-{kind}"
            try:
                result = submit_one(domain, kind, marker)
            except Exception as error:
                result = {
                    "domain": domain,
                    "kind": kind,
                    "marker": marker,
                    "accepted": False,
                    "error": str(error),
                    "submitted_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                }
            upsert_submission(checkpoint["submissions"], result)
            _write_checkpoint(args.output, checkpoint)
            status = "ACCEPTED" if result.get("accepted") else "FAILED"
            print(f"{domain} {kind}: {status}", flush=True)
            if not result.get("accepted"):
                failed.append(f"{domain}:{kind}")

    _write_checkpoint(args.output, checkpoint)
    print(json.dumps({"failed": failed, **checkpoint["summary"]}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
