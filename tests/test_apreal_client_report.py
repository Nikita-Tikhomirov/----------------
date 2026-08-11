from __future__ import annotations

import json
import inspect
from pathlib import Path

import pytest


def test_migration_scope_is_complete_without_hiding_exceptions():
    from tools import build_apreal_client_report as report

    groups = [
        set(report.MIGRATIONS_LIVE),
        set(report.MIGRATIONS_SOURCE_PLACEHOLDER),
        set(report.MIGRATIONS_STAGED),
        set(report.MIGRATIONS_BLOCKED),
        set(report.MIGRATIONS_SCOPE_DECISION),
        set(report.MIGRATIONS_EXCLUDED),
    ]

    assert sum(len(group) for group in groups) == 35
    assert len(set().union(*groups)) == 35
    assert "othodi-spb.ru" not in report.MIGRATIONS_LIVE
    assert "othodi-spb.ru" in report.MIGRATIONS_SOURCE_PLACEHOLDER
    assert "mchs-vrn.ru" in report.MIGRATIONS_STAGED
    assert report.MIGRATIONS_SCOPE_DECISION == []
    assert report.MIGRATIONS_EXCLUDED == ["elektro.spb.ru"]
    assert report.MIGRATIONS_ADDITIONAL == ["39mchs.ru"]


def test_client_input_requests_are_specific_and_do_not_repeat_resolved_scope_questions():
    from tools import build_apreal_client_report as report

    requested = {item[0] for item in report.CLIENT_INPUT_REQUIRED}

    assert requested == {
        "dpocenter.ru",
        "feo-edem.ru",
        "linkedin.com.moopb.ru",
        "mchs-vrn.ru",
        "aklab-spb.ru",
        "othodi-spb.ru",
    }
    assert "elektro.spb.ru" not in requested
    assert "apreal-samara.ru" not in requested
    assert not any("ivideon" in item[0].casefold() for item in report.CLIENT_INPUT_REQUIRED)


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


def test_client_report_delivery_loader_uses_complete_post_send_matrix(tmp_path, monkeypatch):
    from tools import build_apreal_client_report as report

    delivery_path = tmp_path / "delivery.json"
    delivery_path.write_text(
        json.dumps(
            {
                "submissions": [
                    {"domain": "example.ru", "kind": "callback", "accepted": True},
                    {"domain": "example.ru", "kind": "question", "accepted": True},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(report, "SENDER_DELIVERY_PATH", delivery_path)

    assert set(report.load_delivery_index()) == {
        ("example.ru", "callback"),
        ("example.ru", "question"),
    }


def test_finalize_audit_requires_complete_visual_review_manifest(tmp_path, monkeypatch):
    from pypdf import PdfWriter

    from tools import build_apreal_client_report as report

    output_audit = tmp_path / "audit.json"
    output_docx = tmp_path / "report.docx"
    output_pdf = tmp_path / "report.pdf"
    internal_note = tmp_path / "note.md"

    output_audit.write_text('{"status": "docx_generated"}', encoding="utf-8")
    for path in (output_docx, internal_note):
        path.write_bytes(b"test")

    report_writer = PdfWriter()
    report_writer.add_blank_page(width=100, height=100)
    report_writer.add_blank_page(width=100, height=100)
    with output_pdf.open("wb") as stream:
        report_writer.write(stream)

    for name, value in {
        "ROOT": tmp_path,
        "OUTPUT_AUDIT": output_audit,
        "OUTPUT_DOCX": output_docx,
        "OUTPUT_PDF": output_pdf,
        "INTERNAL_NOTE": internal_note,
    }.items():
        monkeypatch.setattr(report, name, value)

    pending = report.finalize_audit()
    assert pending["visual_review"]["all_pages_reviewed"] is False
    assert pending["visual_review"]["result"] == "pending"

    manifest = tmp_path / "visual-review.json"
    manifest.write_text(
        json.dumps(
            {
                "reviewer": "test reviewer",
                "reviewed_at": "2026-08-03T02:00:00+03:00",
                "client_report_pages": [1, 2],
            }
        ),
        encoding="utf-8",
    )
    verified = report.finalize_audit(manifest)
    assert verified["visual_review"]["all_pages_reviewed"] is True
    assert verified["visual_review"]["result"] == "passed"


def test_report_never_turns_handler_acceptance_into_universal_mailbox_delivery():
    from tools import build_apreal_client_report as report

    requirement_text = " ".join(detail for _, detail in report.FORM_REQUIREMENTS)
    docx_delivery_source = inspect.getsource(report.add_human_mail)
    pdf_source = (Path(__file__).resolve().parents[1] / "tools" / "build_apreal_client_pdf.py").read_text(
        encoding="utf-8"
    )
    pdf_delivery_source = pdf_source.rsplit("def build_report_pdf()", 1)[1]
    client_visible_source = (
        inspect.getsource(report.add_human_report_cover)
        + docx_delivery_source
        + pdf_delivery_source
    )

    assert report.MAIL_DELIVERY_SCOPE == "mailbox_confirmed_sites_only"
    assert report.MAILBOX_CONFIRMED_SITES == ("medlic.spb.ru",)
    assert "Все 60 контрольных писем найдены" not in requirement_text
    assert "handler acceptance" not in requirement_text.lower()
    assert "medlic.spb.ru" in docx_delivery_source
    assert "medlic.spb.ru" in pdf_delivery_source

    unsupported_claims = (
        "60 из 60 контрольных писем",
        "60 из 60 писем",
        "писем получены",
        "писем найдены",
        "письма найдены в почте",
        "Получение подтверждено поиском писем в целевых ящиках",
        "56 писем в основной итоговой выборке",
        "56 полученных писем",
        "56 сообщений основного прогона",
        "60\", \"получено",
        "0\", \"потеряно",
        '"mailbox_messages": 60',
        "56 main messages + 4 route-control messages",
        "60/60 сообщений найдены",
        "60 валидных заявок приняты и 60 писем найдены",
        '"mailbox_messages_found": 60',
        "подтвердил получение писем",
    )
    for claim in unsupported_claims:
        assert claim.casefold() not in client_visible_source.casefold()

    assert "личного gmail" in client_visible_source.casefold()
    assert (
        "прямую доставку в ящик отдельно показываю только для medlic.spb.ru"
        in client_visible_source.casefold()
    )


def test_client_report_does_not_expose_internal_video_work():
    from tools import build_apreal_client_report as report

    pdf_source = (Path(__file__).resolve().parents[1] / "tools" / "build_apreal_client_pdf.py").read_text(
        encoding="utf-8"
    )
    pdf_visible_source = pdf_source.rsplit("def build_report_pdf()", 1)[1]
    combined_source = (
        " ".join(" ".join(item) for item in report.HUMAN_CORRECTIONS)
        + inspect.getsource(report.add_human_report_cover)
        + inspect.getsource(report.add_human_mail)
        + pdf_visible_source
    ).casefold()

    for internal_topic in (
        "фоновое видео",
        "видеофон",
        "ivideon",
        "движущимися цветными шарами",
        "background video",
    ):
        assert internal_topic not in combined_source


def test_client_visible_text_is_plain_and_has_no_old_metric_strip():
    from tools import build_apreal_client_report as report

    pdf_source = (Path(__file__).resolve().parents[1] / "tools" / "build_apreal_client_pdf.py").read_text(
        encoding="utf-8"
    )
    pdf_visible_source = pdf_source.rsplit("def build_report_pdf()", 1)[1]

    visible = (
        inspect.getsource(report.add_human_report_cover)
        + inspect.getsource(report.add_human_corrections)
        + pdf_visible_source
    ).casefold()

    for stale in (
        "60 из 60",
        "48 из 48",
        "полностью пересобрал контроль",
        "автоматические проверки показывали",
        "маршрутизация заявок",
    ):
        assert stale not in visible

    assert "что было не так" in visible
    assert "что исправлено" in visible
