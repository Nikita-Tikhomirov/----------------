"""Validate that client tasks have enough evidence for their status."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


FINAL_STATUSES = {"verifying", "awaiting_user_release", "client_review", "accepted"}
VALID_STATUSES = {
    "new",
    "awaiting_user_approval",
    "in_progress",
    "blocked",
    *FINAL_STATUSES,
}
WORK_STARTED_STATUSES = {
    "in_progress",
    "verifying",
    "awaiting_user_release",
    "client_review",
    "accepted",
}
RELEASE_EVIDENCE_STATUSES = {"awaiting_user_release", "client_review", "accepted"}
MATRIX_STATUSES = {"pending", "in_progress", "passed", "blocked", "excluded"}
VALID_FINANCIAL_CLASSES = {
    "main_package",
    "acceptance_fix",
    "warranty_fix",
    "new_work",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nested(record: dict[str, Any], *keys: str) -> Any:
    current: Any = record
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not value:
        return None
    if not all(_nonempty(item) for item in value):
        return None
    return value


def _validate_workflow_v2(task: dict[str, Any], task_id: str, status: Any) -> list[str]:
    """Validate owner gates and exact requirement/site coverage for workflow v2."""
    errors: list[str] = []
    if status == "new":
        return errors

    if not _nonempty(_nested(task, "request", "email_message_id")):
        errors.append(f"{task_id}: workflow v2 request is missing email message id")
    if not _nonempty(_nested(task, "request", "thread_id")):
        errors.append(f"{task_id}: workflow v2 request is missing thread id")

    specification = task.get("specification")
    if not isinstance(specification, dict):
        return [*errors, f"{task_id}: specification must be an object"]
    if not _nonempty(specification.get("title")):
        errors.append(f"{task_id}: specification is missing title")
    if _string_list(specification.get("source_message_ids")) is None:
        errors.append(f"{task_id}: specification source_message_ids must be a non-empty list")

    sites = _string_list(specification.get("sites"))
    if sites is None:
        errors.append(f"{task_id}: specification sites must be a non-empty list")
        sites = []
    site_set = set(sites)

    requirements = specification.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        errors.append(f"{task_id}: specification requirements must be a non-empty list")
        requirements = []

    requirement_sites: dict[str, set[str]] = {}
    for requirement in requirements:
        if not isinstance(requirement, dict) or not _nonempty(requirement.get("id")):
            errors.append(f"{task_id}: specification requirement is missing id")
            continue
        requirement_id = requirement["id"]
        if requirement_id in requirement_sites:
            errors.append(f"{task_id}: duplicate specification requirement {requirement_id}")
            continue
        if not _nonempty(requirement.get("description")):
            errors.append(f"{task_id}: requirement {requirement_id} is missing description")
        raw_scoped_sites = requirement.get("sites")
        scoped_sites = sites if raw_scoped_sites == ["*"] else _string_list(raw_scoped_sites)
        if scoped_sites is None:
            errors.append(f"{task_id}: requirement {requirement_id} sites must be a non-empty list")
            scoped_sites = []
        for site in scoped_sites:
            if site not in site_set:
                errors.append(f"{task_id}: requirement {requirement_id} references unknown site {site}")
        if _string_list(requirement.get("acceptance_criteria")) is None:
            errors.append(f"{task_id}: requirement {requirement_id} is missing acceptance criteria")
        requirement_sites[requirement_id] = set(scoped_sites)

    matrix = specification.get("site_matrix")
    if not isinstance(matrix, list) or not matrix:
        errors.append(f"{task_id}: specification site_matrix must be a non-empty list")
        matrix = []

    covered_pairs: set[tuple[str, str]] = set()
    release_ready = status in RELEASE_EVIDENCE_STATUSES
    for row in matrix:
        if not isinstance(row, dict) or not _nonempty(row.get("site")):
            errors.append(f"{task_id}: specification matrix row is missing site")
            continue
        site = row["site"]
        if site not in site_set:
            errors.append(f"{task_id}: specification matrix references unknown site {site}")
        requirement_ids = _string_list(row.get("requirement_ids"))
        if requirement_ids is None:
            errors.append(f"{task_id}: specification matrix row {site} has no requirement_ids")
            continue
        row_status = row.get("status")
        if row_status not in MATRIX_STATUSES:
            errors.append(f"{task_id}: specification matrix row {site} has invalid status")
        if release_ready and row_status not in {"passed", "excluded"}:
            errors.append(f"{task_id}: specification matrix row {site} is not complete")
        if release_ready and row_status == "passed" and _string_list(row.get("evidence")) is None:
            errors.append(f"{task_id}: specification matrix row {site} is missing evidence")
        if row_status == "excluded" and not _nonempty(row.get("authorization")):
            errors.append(f"{task_id}: excluded matrix row {site} lacks authorization")

        for requirement_id in requirement_ids:
            pair = (requirement_id, site)
            if requirement_id not in requirement_sites:
                errors.append(f"{task_id}: specification matrix references unknown requirement {requirement_id}")
            elif site not in requirement_sites[requirement_id]:
                errors.append(f"{task_id}: specification matrix has out-of-scope pair {requirement_id}@{site}")
            if pair in covered_pairs:
                errors.append(f"{task_id}: duplicate specification matrix row {requirement_id}@{site}")
            covered_pairs.add(pair)

    expected_pairs = {
        (requirement_id, site)
        for requirement_id, scoped_sites in requirement_sites.items()
        for site in scoped_sites
    }
    for requirement_id, site in sorted(expected_pairs - covered_pairs):
        errors.append(f"{task_id}: missing specification matrix row {requirement_id}@{site}")

    approval = task.get("owner_approval")
    approval_status = approval.get("status") if isinstance(approval, dict) else None
    if status == "awaiting_user_approval" and approval_status != "pending":
        errors.append(f"{task_id}: awaiting_user_approval must have pending owner approval")
    if status in WORK_STARTED_STATUSES and (
        approval_status != "approved" or not _nonempty(_nested(task, "owner_approval", "evidence"))
    ):
        errors.append(f"{task_id}: work started without explicit owner approval")

    release = task.get("owner_release")
    release_status = release.get("status") if isinstance(release, dict) else None
    if status == "awaiting_user_release" and release_status != "pending":
        errors.append(f"{task_id}: awaiting_user_release must have pending owner release")
    if status in {"client_review", "accepted"} and (
        release_status != "approved" or not _nonempty(_nested(task, "owner_release", "evidence"))
    ):
        errors.append(f"{task_id}: client contact occurred without explicit owner release")

    client_report_id = _nested(task, "client_report", "email_message_id")
    if _nonempty(client_report_id) and release_status != "approved":
        errors.append(f"{task_id}: client report exists before explicit owner release")

    if status not in {"client_review", "accepted"} and _nested(task, "contact_policy", "status") != "blocked_by_user":
        errors.append(f"{task_id}: client contact must remain blocked before owner release")

    if release_ready:
        report = task.get("evidence_report")
        if not isinstance(report, dict) or report.get("status") != "verified":
            errors.append(f"{task_id}: evidence report must be verified")
        else:
            for field in ("docx", "pdf", "audit"):
                if not _nonempty(report.get(field)):
                    errors.append(f"{task_id}: evidence report is missing {field}")

    return errors


def validate_register(registry: dict[str, Any], root: Path | None = None) -> list[str]:
    """Return human-readable errors for incomplete task evidence."""
    del root  # Evidence may be on the live server or in Gmail, not only locally.
    errors: list[str] = []
    tasks = registry.get("tasks")

    if not isinstance(tasks, list) or not tasks:
        return ["register: tasks must be a non-empty list"]

    task_ids = [task.get("id") for task in tasks if isinstance(task, dict)]
    duplicate_ids = [task_id for task_id, count in Counter(task_ids).items() if task_id and count > 1]
    if duplicate_ids:
        errors.extend(f"register: duplicate task id {task_id}" for task_id in duplicate_ids)

    for task in tasks:
        if not isinstance(task, dict):
            errors.append("register: task must be an object")
            continue

        task_id = task.get("id")
        if not _nonempty(task_id):
            errors.append("register: task is missing id")
            continue

        status = task.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{task_id}: invalid status {status!r}")

        if task.get("financial_classification") not in VALID_FINANCIAL_CLASSES:
            errors.append(f"{task_id}: invalid financial classification")

        workflow_version = task.get("workflow_version", 1)
        if workflow_version not in {1, 2}:
            errors.append(f"{task_id}: invalid workflow version {workflow_version!r}")
        elif workflow_version == 2:
            errors.extend(_validate_workflow_v2(task, task_id, status))

        if task.get("reopened"):
            if not _nonempty(_nested(task, "prevention", "root_cause")):
                errors.append(f"{task_id}: reopened task is missing prevention root cause")
            if not _nonempty(_nested(task, "prevention", "regression_protection")):
                errors.append(f"{task_id}: reopened task is missing regression protection")

        if status not in FINAL_STATUSES:
            continue

        if not _nonempty(_nested(task, "request", "email_message_id")):
            errors.append(f"{task_id}: missing source email message id")
        if not _nonempty(_nested(task, "backup", "location")):
            errors.append(f"{task_id}: missing backup location")
        if not _nonempty(_nested(task, "publication", "live_url")):
            errors.append(f"{task_id}: missing published live URL")

        functional = _nested(task, "verification", "functional")
        if not isinstance(functional, list) or not functional:
            errors.append(f"{task_id}: missing functional verification")
        if not _nonempty(_nested(task, "verification", "visual", "desktop")):
            errors.append(f"{task_id}: missing desktop visual evidence")
        if not _nonempty(_nested(task, "verification", "visual", "mobile")):
            errors.append(f"{task_id}: missing mobile visual evidence")

        if status in {"client_review", "accepted"} and not _nonempty(
            _nested(task, "client_report", "email_message_id")
        ):
            errors.append(f"{task_id}: missing client report message id")

        if status == "accepted":
            acceptance = _nested(task, "client_acceptance")
            has_acceptance = isinstance(acceptance, dict) and any(
                _nonempty(acceptance.get(field)) for field in ("email_message_id", "evidence")
            )
            if not has_acceptance:
                errors.append(f"{task_id}: accepted task is missing client acceptance evidence")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "register",
        nargs="?",
        default="client_tasks.json",
        type=Path,
        help="path to the machine-readable client task register",
    )
    args = parser.parse_args()

    try:
        registry = json.loads(args.register.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read {args.register}: {error}")
        return 2

    errors = validate_register(registry, root=Path.cwd())
    if errors:
        print("Client task quality gate failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    counts = Counter(task["status"] for task in registry["tasks"])
    summary = ", ".join(f"{status}={count}" for status, count in sorted(counts.items()))
    print(f"Client task quality gate passed: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
