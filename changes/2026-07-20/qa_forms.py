#!/usr/bin/env python3
"""Rendered desktop/mobile QA for all application-form sites."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

from playwright.sync_api import sync_playwright


BASE = Path(__file__).resolve().parent
SCOPE = json.loads((BASE / "form-audit-scope.json").read_text(encoding="utf-8"))
OUTPUT = BASE / "browser-qa-results.json"
SCREENSHOT_DIR = Path(tempfile.gettempdir()) / "beget-form-qa-2026-07-20"
SCREENSHOT_DOMAINS = {
    "docp.ru",
    "fste.ru",
    "lfsb.ru",
    "medtex39.ru",
    "ed-kgd.ru",
    "shopap.ru",
}


def visible_count(locator) -> int:
    return sum(
        1
        for index in range(locator.count())
        if locator.nth(index).is_visible()
    )


def inspect_standard_component(page, domain: str, result: dict) -> bool:
    if page.locator(".csf-root").count() == 0:
        return False

    callback_button = page.locator(".csf-open-callback").first
    question_button = page.locator(".csf-open-question").first
    result["callback_buttons"] = visible_count(
        page.locator(".csf-open-callback")
    )
    result["question_buttons"] = visible_count(
        page.locator(".csf-open-question")
    )
    if not callback_button.is_visible() or not question_button.is_visible():
        raise RuntimeError("Standard form actions are not visible")

    callback_button.click()
    callback = page.locator('.csf-modal[data-modal="callback"]')
    callback.wait_for(state="visible", timeout=5000)
    result["callback"] = {
        "title": callback.locator("h2").inner_text().strip(),
        "phone": callback.locator('input[name="phone"]').count(),
        "captcha": callback.locator('input[name="captcha"]').count(),
        "policy": callback.locator(
            'a[href="https://www.apreal.ru/konfedencialnost.html"]'
        ).count(),
        "close": callback.locator(".csf-close").count(),
    }
    if domain in SCREENSHOT_DOMAINS:
        target = SCREENSHOT_DIR / f"{domain}-callback-desktop.png"
        page.screenshot(path=str(target), full_page=False)
        result["screenshots"].append(str(target))
    callback.locator(".csf-close").click()

    question_button.click()
    question = page.locator('.csf-modal[data-modal="question"]')
    question.wait_for(state="visible", timeout=5000)
    result["question"] = {
        "title": question.locator("h2").inner_text().strip(),
        "email": question.locator('input[name="email"]').count(),
        "optional_question": question.locator(
            'textarea[name="question"]'
        ).count(),
        "captcha": question.locator('input[name="captcha"]').count(),
        "policy": question.locator(
            'a[href="https://www.apreal.ru/konfedencialnost.html"]'
        ).count(),
        "close": question.locator(".csf-close").count(),
    }
    question.locator(".csf-close").click()

    page.set_viewport_size({"width": 390, "height": 844})
    callback_button.click()
    callback.wait_for(state="visible", timeout=5000)
    box = callback.bounding_box()
    result["mobile"] = {
        "modal_visible": callback.is_visible(),
        "fits_viewport": bool(
            box
            and box["x"] >= 0
            and box["y"] >= 0
            and box["x"] + box["width"] <= 390
            and box["y"] + box["height"] <= 844
        ),
    }
    if domain in SCREENSHOT_DOMAINS:
        target = SCREENSHOT_DIR / f"{domain}-callback-mobile.png"
        page.screenshot(path=str(target), full_page=False)
        result["screenshots"].append(str(target))
    callback.locator(".csf-close").click()
    page.set_viewport_size({"width": 1280, "height": 800})
    return True


def inspect_existing(page, result: dict) -> None:
    body = " ".join(page.locator("body").inner_text().split())
    result["existing"] = {
        "callback_label": "ЗАКАЗАТЬ ЗВОНОК" in body.upper(),
        "question_label": "ЗАДАТЬ ВОПРОС" in body.upper(),
        "consent": "я даю согласие на обработку персональных данных" in body.lower(),
        "policy": page.locator(
            'a[href="https://www.apreal.ru/konfedencialnost.html"]'
        ).count()
        > 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    sites = [
        site
        for site in SCOPE["sites"]
        if not args.domain or site["domain"] == args.domain
    ]
    if not sites:
        parser.error(f"Domain is not in the QA scope: {args.domain}")

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for site in sites:
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/124 Safari/537.36"
                ),
                ignore_https_errors=True,
                service_workers="block",
            )
            page = context.new_page()
            page.set_default_timeout(10000)
            result = {
                "domain": site["domain"],
                "url": "",
                "title": "",
                "status": 0,
                "meaningful_body": False,
                "standard_component": False,
                "callback_buttons": 0,
                "question_buttons": 0,
                "console_errors": [],
                "page_errors": [],
                "screenshots": [],
                "error": "",
            }
            page.on(
                "console",
                lambda message, item=result: item["console_errors"].append(
                    message.text
                )
                if message.type == "error"
                else None,
            )
            page.on(
                "pageerror",
                lambda error, item=result: item["page_errors"].append(
                    str(error)
                ),
            )
            try:
                response = page.goto(
                    f"https://{site['domain']}/",
                    wait_until="commit",
                    timeout=15000,
                )
                page.wait_for_timeout(2500)
                result["url"] = page.url
                result["title"] = page.title()
                result["status"] = response.status if response else 0
                result["meaningful_body"] = (
                    len(page.locator("body").inner_text().strip()) > 100
                )
                result["standard_component"] = inspect_standard_component(
                    page,
                    site["domain"],
                    result,
                )
                if not result["standard_component"]:
                    inspect_existing(page, result)
            except Exception as error:
                result["error"] = str(error)
            finally:
                results.append(result)
                page.close()
                context.close()
                args.output.write_text(
                    json.dumps(
                        {
                            "screenshot_dir": str(SCREENSHOT_DIR),
                            "results": results,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                print(
                    f"{len(results)}/{len(sites)} "
                    f"{site['domain']} "
                    f"{'ERROR' if result['error'] else 'OK'}",
                    flush=True,
                )
        browser.close()

    args.output.write_text(
        json.dumps(
            {"screenshot_dir": str(SCREENSHOT_DIR), "results": results},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    failed = [
        item
        for item in results
        if item["error"]
        or item["status"] != 200
        or not item["meaningful_body"]
        or (
            item["standard_component"]
            and (
                not item.get("mobile", {}).get("modal_visible")
                or not item.get("mobile", {}).get("fits_viewport")
            )
        )
    ]
    print(
        json.dumps(
            {
                "total": len(results),
                "standard_components": sum(
                    item["standard_component"] for item in results
                ),
                "failed": [
                    {
                        "domain": item["domain"],
                        "status": item["status"],
                        "error": item["error"],
                        "mobile": item.get("mobile"),
                    }
                    for item in failed
                ],
                "screenshot_dir": str(SCREENSHOT_DIR),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
