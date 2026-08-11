from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LIVE_GATE = ROOT / "tests/live_apreal_portfolio_acceptance.cjs"


def source() -> str:
    return LIVE_GATE.read_text(encoding="utf-8")


def test_live_gate_uses_clean_urls_and_enforces_tls():
    text = source()

    assert "ignoreHTTPSErrors: true" not in text
    assert "full_acceptance=" not in text
    assert "page.goto(`https://${domain}/`" in text


def test_live_gate_treats_runtime_and_resource_errors_as_failures():
    text = source()

    assert "result.failures.push(...result.pageErrors" in text
    assert "result.failures.push(...result.criticalConsoleErrors" in text
    assert "page.on('requestfailed'" in text
    assert "page.on('response'" in text
    assert "pre-existing page error" not in text


def test_live_gate_does_not_fail_sites_for_third_party_resource_console_noise():
    text = source()

    assert "isCriticalConsoleError(message, sourceUrl, domain)" in text
    assert "isFirstParty(sourceUrl, domain)" in text
    assert "isCriticalConsoleError(value, location.url, domain)" in text


def test_live_gate_records_canonical_url_and_viewport_screenshots():
    text = source()

    assert "canonicalUrl" in text
    assert "fullPage: false" in text


def test_live_gate_can_process_independent_sites_concurrently():
    text = source()

    assert "QA_CONCURRENCY" in text
    assert "Promise.all(workers)" in text


def test_live_gate_bounds_screenshots_and_records_console_locations():
    text = source()

    assert "QA_SCREENSHOT_TIMEOUT_MS" in text
    assert "animations: 'disabled'" in text
    assert "consoleErrorDetails" in text
    assert "message.location()" in text


def test_live_gate_requires_controls_to_fill_the_form_content_width():
    text = source()

    assert "formInnerWidth" in text
    assert "does not fill form width" in text


def test_live_gate_waits_for_smart_slider_before_visual_capture():
    text = source()

    assert "QA_VISUAL_STABILITY_TIMEOUT_MS" in text
    assert "waitForVisualStability" in text
    assert "n2-ss-loaded" in text
    assert "visual loading state did not settle: Smart Slider 3" in text
    assert text.index("await waitForVisualStability(page, result)") < text.index(
        "result.pageScreenshot = await screenshot(page, domain, viewport.name, 'page')"
    )


def test_live_gate_retries_isolated_browser_crashes_without_aborting_matrix():
    text = source()

    assert "QA_ATTEMPTS" in text
    assert "isRetryableBrowserFailure" in text
    assert "auditViewWithRetry" in text
    assert "browser infrastructure failure after" in text
    assert "await context.close().catch" in text
    assert "const result = await auditViewWithRetry" in text


def test_live_gate_falls_back_when_primary_headless_browser_cannot_start():
    text = source()

    assert "launchAuditBrowser" in text
    assert "C:/Program Files/Google/Chrome/Application/chrome.exe" in text
    assert "browser launch failed for all configured executables" in text
    assert "const browser = await launchAuditBrowser()" in text
