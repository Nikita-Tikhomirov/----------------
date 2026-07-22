#!/usr/bin/env python3
"""Capture desktop and mobile QA evidence for medtex39.ru forms."""

from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = "https://medtex39.ru/?visual-qa=20260722"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
OUTPUT = Path(__file__).resolve().parents[2] / "tmp" / "medtex39-antispam"


def inspect_modal(page, kind: str) -> dict:
    page.locator(f".csf-open-{kind}").first.click()
    modal = page.locator(f'.csf-modal[data-modal="{kind}"]')
    modal.wait_for(state="visible")
    page.wait_for_function(
        "kind => document.querySelector(`[data-modal=\"${kind}\"] [name=\"form_token\"]`).value.length > 20",
        arg=kind,
    )
    return modal.evaluate(
        """modal => {
            const box = modal.getBoundingClientRect();
            const fields = [...modal.querySelectorAll('input,textarea')]
                .filter(field => field.type !== 'hidden')
                .map(field => field.name);
            return {
                heading: modal.querySelector('h2').textContent.trim(),
                fields,
                tokenLength: modal.querySelector('[name="form_token"]').value.length,
                insideViewport: box.left >= 0 && box.top >= 0
                    && box.right <= innerWidth && box.bottom <= innerHeight,
                submitEnabled: !modal.querySelector('.csf-submit').disabled,
            };
        }"""
    )


def run_viewport(browser, name: str, width: int, height: int) -> dict:
    context = browser.new_context(viewport={"width": width, "height": height})
    page = context.new_page()
    console_errors = []
    failed_responses = []
    page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
    page.on(
        "response",
        lambda response: failed_responses.append(
            {"status": response.status, "url": response.url}
        )
        if response.status >= 400
        else None,
    )
    page.goto(URL, wait_until="networkidle")
    page.locator(".csf-actions").wait_for(state="visible")

    callback = inspect_modal(page, "callback")
    page.screenshot(path=str(OUTPUT / f"{name}-callback.png"), full_page=False)
    page.locator('.csf-modal[data-modal="callback"] .csf-close').click()

    question = inspect_modal(page, "question")
    page.screenshot(path=str(OUTPUT / f"{name}-question.png"), full_page=False)

    result = {
        "viewport": {"width": width, "height": height},
        "callback": callback,
        "question": question,
        "legacyForms": page.locator('form[action*="tomt_dir.php"]').count(),
        "consoleErrors": console_errors,
        "failedResponses": failed_responses,
    }
    context.close()
    return result


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(CHROME),
            headless=True,
        )
        try:
            results = {
                "desktop": run_viewport(browser, "desktop", 1440, 900),
                "mobile": run_viewport(browser, "mobile", 390, 844),
            }
        finally:
            browser.close()

    result_path = OUTPUT / "results.json"
    result_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(results, ensure_ascii=False))

    for viewport in results.values():
        relevant_failures = [
            failure
            for failure in viewport["failedResponses"]
            if "client-standard" in failure["url"]
        ]
        assert not relevant_failures
        for kind in ("callback", "question"):
            assert viewport[kind]["insideViewport"]
            assert viewport[kind]["submitEnabled"]
            assert viewport[kind]["tokenLength"] >= 48
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
