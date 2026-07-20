#!/usr/bin/env python3
"""Read-only public audit for the client's application-form requirements."""

from __future__ import annotations

import argparse
import html
import json
import re
import ssl
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler, HTTPSHandler


CALLBACK_LABEL = "заказать звонок"
QUESTION_LABEL = "задать вопрос"
CONSENT_FRAGMENT = "я даю согласие на обработку персональных данных"
POLICY_PATH = "apreal.ru/konfedencialnost.html"
SUCCESS_MESSAGE = "спасибо за ваше сообщение. оно успешно отправлено"
LEGACY_LABELS = (
    "бесплатная консультация",
    "расчет стоимости",
    "расчёт стоимости",
    "оставить заявку",
    "обратный звонок",
)


def normalize_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def detect_features(page_html: str) -> dict[str, bool]:
    text = normalize_text(page_html)
    compact_html = re.sub(r"\s+", "", html.unescape(page_html)).lower()
    return {
        "callback_label": CALLBACK_LABEL in text,
        "question_label": QUESTION_LABEL in text,
        "consent": CONSENT_FRAGMENT in text,
        "policy_link": POLICY_PATH in compact_html,
        "success_message": SUCCESS_MESSAGE in text,
        "legacy_labels": any(label in text for label in LEGACY_LABELS),
    }


def fetch(domain: str, timeout: int = 20) -> dict[str, Any]:
    context = ssl.create_default_context()
    opener = build_opener(HTTPRedirectHandler(), HTTPSHandler(context=context))
    last_error = ""
    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}/"
        request = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 FormAudit/2026-07-20"},
        )
        try:
            with opener.open(request, timeout=timeout) as response:
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
                try:
                    body = raw.decode(charset, errors="replace")
                except LookupError:
                    body = raw.decode("utf-8", errors="replace")
                return {
                    "requested_url": url,
                    "final_url": response.geturl(),
                    "status": response.status,
                    "content_type": response.headers.get("Content-Type", ""),
                    "features": detect_features(body),
                    "body_bytes": len(raw),
                    "error": "",
                }
        except (HTTPError, URLError, TimeoutError, ssl.SSLError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return {
        "requested_url": f"https://{domain}/",
        "final_url": "",
        "status": 0,
        "content_type": "",
        "features": detect_features(""),
        "body_bytes": 0,
        "error": last_error,
    }


def audit(scope: dict[str, Any]) -> dict[str, Any]:
    results = []
    for site in scope["sites"]:
        result = fetch(site["domain"])
        result["domain"] = site["domain"]
        result["expected_recipient"] = site.get("recipient", "")
        results.append(result)
    return {
        "sites": results,
        "excluded": scope.get("excluded", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scope",
        type=Path,
        default=Path(__file__).with_name("form-audit-scope.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    scope = json.loads(args.scope.read_text(encoding="utf-8"))
    result = audit(scope)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
