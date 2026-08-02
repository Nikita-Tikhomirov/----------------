import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.validate_client_tasks import validate_register


def complete_task(status="client_review"):
    task = {
        "id": "medlic-seo-20260725",
        "site": "medlic.spb.ru",
        "status": status,
        "financial_classification": "acceptance_fix",
        "request": {"email_message_id": "19f9a005ec1821e7"},
        "backup": {"location": "/home/n/nousroc9/_backups/example"},
        "publication": {"live_url": "https://medlic.spb.ru/"},
        "verification": {
            "functional": ["HTTP 200"],
            "visual": {
                "desktop": "output/visual-qa/desktop.png",
                "mobile": "output/visual-qa/mobile.png",
            },
        },
        "client_report": {"email_message_id": "19f9a306689f3bcd"},
    }
    if status == "accepted":
        task["client_acceptance"] = {"email_message_id": "19f9a343ceb5b38d"}
    return task


def workflow_v2_task(status="awaiting_user_approval"):
    task = {
        "id": "portfolio-forms-v2",
        "site": "a.ru, b.ru",
        "status": status,
        "workflow_version": 2,
        "financial_classification": "warranty_fix",
        "request": {
            "email_message_id": "message-1",
            "thread_id": "thread-1",
        },
        "specification": {
            "title": "Unify both forms on both sites",
            "source_message_ids": ["message-1"],
            "sites": ["a.ru", "b.ru"],
            "requirements": [
                {
                    "id": "F-01",
                    "description": "Both forms use the exact labels",
                    "sites": ["a.ru", "b.ru"],
                    "acceptance_criteria": ["Exact callback and question labels"],
                }
            ],
            "site_matrix": [
                {
                    "site": "a.ru",
                    "requirement_ids": ["F-01"],
                    "status": "pending",
                    "evidence": [],
                },
                {
                    "site": "b.ru",
                    "requirement_ids": ["F-01"],
                    "status": "pending",
                    "evidence": [],
                },
            ],
        },
        "owner_approval": {"status": "pending"},
        "owner_release": {"status": "pending"},
        "contact_policy": {
            "status": "blocked_by_user",
            "instruction": "No client contact without explicit owner release.",
        },
    }
    if status in {"in_progress", "verifying", "awaiting_user_release", "client_review", "accepted"}:
        task["owner_approval"] = {
            "status": "approved",
            "evidence": "Explicit owner instruction in the Codex task.",
        }
    if status in {"verifying", "awaiting_user_release", "client_review", "accepted"}:
        task.update(
            {
                "backup": {"location": "/backups/task"},
                "publication": {"live_url": "https://a.ru/"},
                "verification": {
                    "functional": ["Both handlers accepted valid requests"],
                    "visual": {
                        "desktop": "output/desktop.png",
                        "mobile": "output/mobile.png",
                    },
                },
            }
        )
    if status in {"awaiting_user_release", "client_review", "accepted"}:
        for row in task["specification"]["site_matrix"]:
            row["status"] = "passed"
            row["evidence"] = [f"output/{row['site']}-evidence.png"]
        task["evidence_report"] = {
            "status": "verified",
            "docx": "output/report.docx",
            "pdf": "output/report.pdf",
            "audit": "output/report-audit.json",
            "mail_delivery_scope": "configuration_and_handler_acceptance_only",
        }
        task["verification"]["mail_evidence"] = {
            "configured_recipient": "output/recipient-matrix.json",
            "handler_acceptance": "output/form-submissions.json",
            "delivery_claim_scope": "configuration_and_handler_acceptance_only",
            "mailbox_confirmed_sites": [],
            "mailbox_evidence": [],
        }
    if status in {"client_review", "accepted"}:
        task["owner_release"] = {
            "status": "approved",
            "evidence": "Explicit owner release in the Codex task.",
        }
        task["client_report"] = {
            "email_message_id": "sent-message-1",
            "sent_at": "2026-08-02T12:00:00+03:00",
        }
    if status == "accepted":
        task["client_acceptance"] = {"evidence": "Client accepted in the original thread."}
    return task


def test_current_register_passes_quality_gate():
    registry = json.loads((ROOT / "client_tasks.json").read_text(encoding="utf-8"))

    assert validate_register(registry, root=ROOT) == []


def test_client_review_requires_both_visual_checkpoints():
    task = complete_task()
    del task["verification"]["visual"]["mobile"]

    errors = validate_register({"tasks": [task]})

    assert "medlic-seo-20260725: missing mobile visual evidence" in errors


def test_accepted_task_requires_client_acceptance_evidence():
    task = complete_task(status="accepted")
    del task["client_acceptance"]

    errors = validate_register({"tasks": [task]})

    assert "medlic-seo-20260725: accepted task is missing client acceptance evidence" in errors


def test_workflow_v2_waiting_for_approval_requires_complete_specification():
    task = workflow_v2_task()
    del task["specification"]["requirements"]

    errors = validate_register({"tasks": [task]})

    assert "portfolio-forms-v2: specification requirements must be a non-empty list" in errors


def test_workflow_v2_cannot_start_without_explicit_owner_approval():
    task = workflow_v2_task(status="in_progress")
    task["owner_approval"] = {"status": "pending"}

    errors = validate_register({"tasks": [task]})

    assert "portfolio-forms-v2: work started without explicit owner approval" in errors


def test_workflow_v2_release_requires_every_requirement_site_pair():
    task = workflow_v2_task(status="awaiting_user_release")
    task["specification"]["site_matrix"] = task["specification"]["site_matrix"][:1]

    errors = validate_register({"tasks": [task]})

    assert "portfolio-forms-v2: missing specification matrix row F-01@b.ru" in errors


def test_workflow_v2_release_requires_verified_evidence_report():
    task = workflow_v2_task(status="awaiting_user_release")
    del task["evidence_report"]["pdf"]

    errors = validate_register({"tasks": [task]})

    assert "portfolio-forms-v2: evidence report is missing pdf" in errors


def test_workflow_v2_forbids_client_report_before_owner_release():
    task = workflow_v2_task(status="awaiting_user_release")
    task["client_report"] = {"email_message_id": "unauthorized-send"}

    errors = validate_register({"tasks": [task]})

    assert "portfolio-forms-v2: client report exists before explicit owner release" in errors


def test_workflow_v2_release_requires_structured_mail_evidence():
    task = workflow_v2_task(status="awaiting_user_release")
    del task["verification"]["mail_evidence"]

    errors = validate_register({"tasks": [task]})

    assert "portfolio-forms-v2: release evidence is missing structured mail evidence" in errors


def test_workflow_v2_cannot_claim_all_mailboxes_from_partial_receipts():
    task = workflow_v2_task(status="awaiting_user_release")
    task["verification"]["mail_evidence"].update(
        {
            "delivery_claim_scope": "mailbox_confirmed_all_sites",
            "mailbox_confirmed_sites": ["a.ru"],
            "mailbox_evidence": ["output/a.ru-mailbox.png"],
        }
    )
    task["evidence_report"]["mail_delivery_scope"] = "mailbox_confirmed_all_sites"

    errors = validate_register({"tasks": [task]})

    assert "portfolio-forms-v2: all-site mailbox claim lacks receipts for b.ru" in errors


def test_workflow_v2_report_mail_scope_must_match_verification_scope():
    task = workflow_v2_task(status="awaiting_user_release")
    task["evidence_report"]["mail_delivery_scope"] = "mailbox_confirmed_all_sites"

    errors = validate_register({"tasks": [task]})

    assert "portfolio-forms-v2: evidence report mail scope does not match verification" in errors


def test_complete_workflow_v2_release_gate_passes():
    assert validate_register({"tasks": [workflow_v2_task(status="awaiting_user_release")]}) == []
