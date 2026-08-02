from __future__ import annotations

import json

import pytest


def test_migration_scope_is_complete_without_hiding_exceptions():
    from tools import build_apreal_client_report as report

    groups = [
        set(report.MIGRATIONS_LIVE),
        set(report.MIGRATIONS_SOURCE_PLACEHOLDER),
        set(report.MIGRATIONS_STAGED),
        set(report.MIGRATIONS_BLOCKED),
        set(report.MIGRATIONS_SCOPE_DECISION),
    ]

    assert sum(len(group) for group in groups) == 35
    assert len(set().union(*groups)) == 35
    assert "othodi-spb.ru" not in report.MIGRATIONS_LIVE
    assert "othodi-spb.ru" in report.MIGRATIONS_SOURCE_PLACEHOLDER
    assert "mchs-vrn.ru" in report.MIGRATIONS_STAGED
    assert report.MIGRATIONS_ADDITIONAL == ["39mchs.ru"]


def test_client_input_requests_are_specific_and_camera_is_not_claimed_fixed():
    from tools import build_apreal_client_report as report

    requested = {item[0] for item in report.CLIENT_INPUT_REQUIRED}

    assert requested == {
        "dpocenter.ru",
        "feo-edem.ru",
        "linkedin.com.moopb.ru",
        "mchs-vrn.ru",
        "aklab-spb.ru",
        "elektro.spb.ru",
        "othodi-spb.ru",
        "nousro.ru / nousro-nn.ru",
        "Ivideon-камера",
        "apreal-samara.ru",
    }
    camera = next(item for item in report.CLIENT_INPUT_REQUIRED if item[0] == "Ivideon-камера")
    assert "не изменялся" in camera[1].lower()
    assert "доступ" in camera[2].lower()


def test_fresh_result_loader_rejects_duplicate_or_failed_views(tmp_path):
    from tools import build_apreal_client_report as report

    results_path = tmp_path / "results.json"
    results_path.write_text(
        json.dumps(
            [
                {
                    "domain": "example.ru",
                    "viewport": "desktop",
                    "status": 200,
                    "failures": [],
                    "pageErrors": [],
                    "criticalConsoleErrors": [],
                    "requestFailures": [],
                },
                {
                    "domain": "example.ru",
                    "viewport": "desktop",
                    "status": 500,
                    "failures": ["failed"],
                    "pageErrors": [],
                    "criticalConsoleErrors": [],
                    "requestFailures": [],
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate QA result"):
        report.load_result_index(results_path)
