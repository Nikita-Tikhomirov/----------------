import sys
import json
import time
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import monitor_live_sites
from tools.monitor_live_sites import check_target, evaluate_response, load_targets


def target(**overrides):
    result = {
        "id": "example-homepage",
        "url": "https://example.ru/",
        "expected_statuses": [200],
        "error_patterns": ["fatal error", "parse error"],
    }
    result.update(overrides)
    return result


def test_successful_page_without_error_markers_is_healthy():
    result = evaluate_response(target(), 200, "<html><body>Working</body></html>", 120)

    assert result["healthy"] is True
    assert result["issues"] == []


def test_http_failure_is_reported_with_target_context():
    result = evaluate_response(target(), 503, "temporarily unavailable", 120)

    assert result["healthy"] is False
    assert result["issues"] == ["unexpected HTTP status 503"]
    assert result["target_id"] == "example-homepage"


def test_fatal_error_marker_fails_even_with_http_200():
    result = evaluate_response(target(), 200, "PHP Fatal error: bad thing", 120)

    assert result["healthy"] is False
    assert result["issues"] == ["page contains error marker: fatal error"]


def test_duplicate_monitor_target_ids_are_rejected(tmp_path):
    config = tmp_path / "targets.json"
    config.write_text(
        json.dumps(
            {
                "targets": [
                    {"id": "duplicate", "url": "https://one.example/"},
                    {"id": "duplicate", "url": "https://two.example/"},
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate monitoring target id"):
        load_targets(config)


def test_monitor_checks_sites_sequentially_to_avoid_shared_host_timeouts(tmp_path, monkeypatch):
    config = tmp_path / "targets.json"
    config.write_text(
        json.dumps(
            {"targets": [{"id": "one", "url": "https://one.example/"}, {"id": "two", "url": "https://two.example/"}]}
        ),
        encoding="utf-8",
    )
    active = 0
    peak_active = 0

    def fake_check(target, timeout_seconds):
        nonlocal active, peak_active
        active += 1
        peak_active = max(peak_active, active)
        time.sleep(0.02)
        active -= 1
        return {"target_id": target["id"], "healthy": True}

    monkeypatch.setattr(monitor_live_sites, "check_target", fake_check)

    monitor_live_sites.run_monitor(config, timeout_seconds=1)

    assert peak_active == 1


def test_check_target_retries_a_transient_network_error(monkeypatch):
    attempts = 0

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"Working"

    def fake_urlopen(request, timeout):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise monitor_live_sites.URLError("temporary DNS failure")
        return Response()

    monkeypatch.setattr(monitor_live_sites, "urlopen", fake_urlopen)

    result = check_target(target(), timeout_seconds=1)

    assert attempts == 2
    assert result["healthy"] is True
