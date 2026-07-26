import sys
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.monitor_live_sites import evaluate_response, load_targets


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
