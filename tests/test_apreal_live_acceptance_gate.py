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
    assert "consoleErrorDetails" in text
    assert "message.location()" in text
