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
