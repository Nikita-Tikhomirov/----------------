# AP-Real Owner-Gated Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the AP-Real cycle read every message through deterministic fallbacks, require owner approval before work, require complete evidence before release, and forbid autonomous client contact.

**Architecture:** Keep Gmail discovery and routing in the existing client-cycle modules, add validated workflow policy to the client profile, and enforce state transitions in the task-register quality gate. The dashboard emits owner-facing actions only for workflow-v2 tasks, while the heartbeat prompt applies the same invariants operationally.

**Tech Stack:** Python 3.10+, JSON registries, pytest, Codex heartbeat automation, Gmail/browser fallback.

## Global Constraints

- Never draft, send, reply to, forward, follow up, or request payment from the client without explicit owner release.
- Never mark a Gmail scan successful while any message ID remains unresolved.
- Never start implementation before explicit owner approval of the complete specification.
- Never mark a multi-site request complete until every requirement/site matrix row has evidence.
- Every frontend requirement needs fresh desktop and mobile visual evidence.

---

### Task 1: Profile and recovery contract

**Files:**
- Modify: `tools/client_message_router.py`
- Modify: `tools/client_cycle.py`
- Modify: `clients/ap-real.json`
- Test: `tests/test_client_message_router.py`

**Interfaces:**
- Consumes: existing `ClientProfile.from_mapping`, ledger `unreadable_messages`.
- Produces: validated `WorkflowPolicy`; `can_mark_scan_success(ledger) -> bool`; explicit `recovery_contract` in cycle JSON.

- [ ] Write tests proving the profile requires both owner gates and that unresolved recovery IDs block scan success.
- [ ] Run `python -m pytest tests/test_client_message_router.py -q` and confirm the new tests fail.
- [ ] Add workflow-policy parsing and replace quarantine wording with an immediate recovery contract covering connector and main-Chrome fallbacks.
- [ ] Reject `--mark-success` when the recovery queue is non-empty.
- [ ] Run the target tests and confirm they pass.

### Task 2: Workflow-v2 register gate

**Files:**
- Modify: `tools/validate_client_tasks.py`
- Test: `tests/test_client_task_register.py`

**Interfaces:**
- Consumes: task objects with `workflow_version: 2`.
- Produces: validation errors for missing specification coverage, approval, visual evidence, evidence report, owner release, or unauthorized client report.

- [ ] Add failing tests for `awaiting_user_approval`, unauthorized `in_progress`, incomplete matrices, and `awaiting_user_release` without evidence.
- [ ] Run `python -m pytest tests/test_client_task_register.py -q` and confirm RED.
- [ ] Add `awaiting_user_approval` and `awaiting_user_release` statuses and workflow-v2 validation helpers.
- [ ] Require each requirement/site pair to exist and be passed before release.
- [ ] Forbid `client_report.email_message_id` before approved owner release.
- [ ] Run the target tests and confirm GREEN.

### Task 3: Owner-only dashboard actions

**Files:**
- Modify: `tools/client_task_dashboard.py`
- Test: `tests/test_client_task_dashboard.py`

**Interfaces:**
- Consumes: validated workflow-v2 tasks.
- Produces: `prepare_specification`, `request_owner_approval`, `continue_work`, `report_blocker_to_owner`, and `request_owner_release` actions.

- [ ] Add failing tests proving workflow-v2 tasks never generate a client-contact action before release.
- [ ] Run `python -m pytest tests/test_client_task_dashboard.py -q` and confirm RED.
- [ ] Implement owner-only queue actions and preserve historical behavior for workflow-v1 records.
- [ ] Run the target tests and confirm GREEN.

### Task 4: Register the completed portfolio work

**Files:**
- Modify: `client_tasks.json`
- Verify: `output/ap-real-report-audit-2026-08-02.json`

**Interfaces:**
- Consumes: the approved AP-Real specification and final 50-page evidence report.
- Produces: a workflow-v2 task in `awaiting_user_release` with complete requirement/site coverage and no client report.

- [ ] Add owner approval evidence and the exact 30-domain specification matrix reference.
- [ ] Replace stale verification paths with final acceptance, targeted nousro-spb, delivery, DOCX, PDF, and audit paths.
- [ ] Set `owner_release.status=pending`, keep client contact blocked, and remove any automatic follow-up action.
- [ ] Run `python tools/validate_client_tasks.py` and confirm the registry passes.

### Task 5: Update heartbeat policy

**Files:**
- Update existing automation: `qa-3`

**Interfaces:**
- Consumes: the two-gate workflow and existing 30-minute heartbeat schedule.
- Produces: intake/monitoring heartbeat that shows the owner a specification or evidence report but sends nothing externally.

- [ ] Preserve the heartbeat schedule and workspace/thread destination.
- [ ] Require full connector-to-browser recovery for every Gmail ID.
- [ ] Stop new technical work at `awaiting_user_approval` until a later explicit owner command.
- [ ] Stop completed work at `awaiting_user_release` and report artifacts to the owner.
- [ ] Explicitly prohibit all client drafts, replies, sends, forwards, follow-ups, and finance outreach.

### Task 6: Full verification and publication

**Files:**
- Verify all files above plus report artifacts.

**Interfaces:**
- Consumes: completed implementation.
- Produces: passing tests, validated register, committed and pushed changes.

- [ ] Run targeted workflow tests.
- [ ] Run the full pytest suite.
- [ ] Run `C:\Users\user\.codex\scripts\harness.cmd smoke` and `C:\Users\user\.codex\scripts\harness.cmd gate`.
- [ ] Verify the report audit JSON, DOCX/PDF hashes, and 50 rendered pages.
- [ ] Stage only the AP-Real implementation and evidence artifacts, commit with a scoped message, and publish with `tools/git_publish.ps1`.
