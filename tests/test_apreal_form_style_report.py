from __future__ import annotations

import json
from pathlib import Path

import pytest


def _qa_row(domain: str, viewport: str, failures: list[str] | None = None) -> dict[str, object]:
    return {
        "domain": domain,
        "viewport": viewport,
        "status": 200,
        "failures": failures or [],
        "pageErrors": [],
        "criticalConsoleErrors": [],
        "requestFailures": [],
        "forms": {
            "callback": {"screenshot": f"{domain}-{viewport}-callback.png"},
            "question": {"screenshot": f"{domain}-{viewport}-question.png"},
        },
    }


def test_client_text_is_plain_truthful_and_excludes_internal_topics():
    from tools import build_apreal_form_style_report as report

    visible = report.collect_client_visible_text().casefold()

    for required in (
        "что требовалось",
        "что было сделано неправильно",
        "что исправлено сейчас",
        "30 сайтов",
        "компьютере и телефоне",
    ):
        assert required in visible

    for forbidden in (
        "видеофон",
        "фоновое видео",
        "ivideon",
        "агент",
        "нейросет",
        "грыж",
        "60 из 60",
        "48 из 48",
        "все письма доставлены",
        "маршрутизация",
    ):
        assert forbidden not in visible


def test_evidence_batches_cover_each_site_once():
    from tools import build_apreal_form_style_report as report

    domains = [f"site-{index}.ru" for index in range(30)]
    batches = report.build_evidence_batches(domains, batch_size=6)

    assert len(batches) == 5
    assert [domain for batch in batches for domain in batch] == domains


def test_each_site_page_lists_corrections_and_its_recipient():
    from tools import build_apreal_form_style_report as report

    facts = report.site_page_facts("example.ru", "info@example.ru")
    visible = " ".join(facts).casefold()

    assert "example.ru" in visible
    assert "info@example.ru" in visible
    assert "обе формы" in visible
    assert "компьютере и телефоне" in visible
    assert "ширину" in visible
    assert "личных и тестовых адресов нет" in visible


def test_load_qa_results_requires_two_clean_viewports_per_site(tmp_path: Path):
    from tools import build_apreal_form_style_report as report

    valid_path = tmp_path / "valid.json"
    valid_path.write_text(
        json.dumps([_qa_row("example.ru", "desktop"), _qa_row("example.ru", "mobile")]),
        encoding="utf-8",
    )
    loaded = report.load_qa_results(valid_path)
    assert set(loaded) == {("example.ru", "desktop"), ("example.ru", "mobile")}

    failed_path = tmp_path / "failed.json"
    failed_path.write_text(
        json.dumps(
            [_qa_row("example.ru", "desktop", ["field width mismatch"]), _qa_row("example.ru", "mobile")]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="QA failures"):
        report.load_qa_results(failed_path)

    incomplete_path = tmp_path / "incomplete.json"
    incomplete_path.write_text(json.dumps([_qa_row("example.ru", "desktop")]), encoding="utf-8")
    with pytest.raises(ValueError, match="desktop and mobile"):
        report.load_qa_results(incomplete_path)


def test_load_recipient_matrix_rejects_failed_or_personal_routes(tmp_path: Path):
    from tools import build_apreal_form_style_report as report

    valid_path = tmp_path / "valid-routes.json"
    valid_path.write_text(
        json.dumps(
            {
                "summary": {
                    "checks": 2,
                    "passed": 2,
                    "failed": [],
                    "personal_recipient_hits": [],
                    "complete": True,
                },
                "checks": [
                    {
                        "domain": "example.ru",
                        "actual_recipient": "info@example.ru",
                        "expected_recipient": "info@example.ru",
                        "passed": True,
                    },
                    {
                        "domain": "example.ru",
                        "actual_recipient": "info@example.ru",
                        "expected_recipient": "info@example.ru",
                        "passed": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    matrix = report.load_recipient_matrix(valid_path)
    assert matrix["summary"]["complete"] is True

    bad = json.loads(valid_path.read_text(encoding="utf-8"))
    bad["summary"]["personal_recipient_hits"] = ["personal@gmail.com"]
    bad_path = tmp_path / "bad-routes.json"
    bad_path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(ValueError, match="personal or test"):
        report.load_recipient_matrix(bad_path)


def test_report_site_order_matches_qa_and_recipient_coverage(tmp_path: Path):
    from tools import build_apreal_form_style_report as report

    qa = {}
    for domain in ("b.ru", "a.ru"):
        qa[(domain, "desktop")] = _qa_row(domain, "desktop")
        qa[(domain, "mobile")] = _qa_row(domain, "mobile")
    matrix = {
        "expected_sites": {"a.ru": "info@a.ru", "b.ru": "info@b.ru"},
        "checks": [],
        "summary": {"complete": True},
    }

    assert report.report_site_order(qa, matrix) == ["a.ru", "b.ru"]

    matrix["expected_sites"]["c.ru"] = "info@c.ru"
    with pytest.raises(ValueError, match="coverage differs"):
        report.report_site_order(qa, matrix)


def test_finalize_existing_visual_review_requires_matching_pdf_hash(tmp_path: Path, monkeypatch):
    from tools import build_apreal_form_style_report as report

    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"stable report")
    audit = tmp_path / "audit.json"
    audit.write_text(json.dumps({"report": {}, "visual_review": {"result": "pending"}}), encoding="utf-8")
    manifest = tmp_path / "review.json"
    manifest.write_text(
        json.dumps(
            {
                "source_pdf_sha256": report._sha256(pdf),
                "client_report_pages": [1, 2],
                "reviewer": "test",
                "reviewed_at": "2026-08-11T22:00:00+03:00",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(report, "OUTPUT_PDF", pdf)
    monkeypatch.setattr(report, "OUTPUT_AUDIT", audit)
    monkeypatch.setattr(report, "_pdf_page_count", lambda _: 2)

    finalized = report.finalize_existing_visual_review(manifest)
    assert finalized["visual_review"]["result"] == "passed"
    assert finalized["visual_review"]["all_pages_reviewed"] is True

    review = json.loads(manifest.read_text(encoding="utf-8"))
    review["source_pdf_sha256"] = "0" * 64
    manifest.write_text(json.dumps(review), encoding="utf-8")
    with pytest.raises(ValueError, match="PDF hash"):
        report.finalize_existing_visual_review(manifest)
