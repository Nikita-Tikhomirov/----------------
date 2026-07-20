# Finish Client Form Requests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish every applicable form request from the client's July 18-20 correspondence, verify each result, and send an evidence-based completion reply.

**Architecture:** Treat the client's table as the source of scope, with explicit exclusions for sites marked "application not needed." Audit public pages and server configuration before changing anything, back up every changed file/database row, make minimal site-specific fixes, then verify page behavior and mail acceptance.

**Tech Stack:** WordPress, Contact Form 7, legacy PHP form handlers, SSH/SFTP on Beget, MySQL, HTTP smoke checks, Python verification scripts, Gmail connector.

## Global Constraints

- Do not change PHP versions.
- Do not alter sites explicitly marked by the client as not needing application forms.
- Preserve existing recipient mailboxes and forwarding; do not redirect applications to the operator's Gmail.
- Do not reuse DKIM keys between domains.
- Do not commit secrets, `Упавшая сессия.txt`, or the local `harness/` directory.
- Back up every production artifact before modifying it.

---

### Task 1: Build the authoritative scope and baseline

**Files:**
- Create: `changes/2026-07-20/form-audit-scope.json`
- Create: `changes/2026-07-20/audit_forms.py`

**Interfaces:**
- Consumes: client table, July 19 reports, live Beget site roots.
- Produces: one JSON audit result per applicable domain and a separate exclusion list.

- [ ] **Step 1: Encode the expected domains, recipients, form requirements, and exclusions.**
- [ ] **Step 2: Write audit assertions for HTTP status, visible form actions, recipients, and success behavior.**
- [ ] **Step 3: Run the audit and save the unmodified baseline.**

### Task 2: Diagnose and fix only confirmed gaps

**Files:**
- Create: `changes/2026-07-20/apply_form_fixes.php` only if shared WordPress changes are required.
- Modify: site-specific files copied under `changes/2026-07-20/<domain>/`.

**Interfaces:**
- Consumes: failed checks from Task 1.
- Produces: minimal production changes with a timestamped server backup.

- [ ] **Step 1: Reproduce each failed form or delivery path and identify its root cause.**
- [ ] **Step 2: Add a focused regression check that fails for the confirmed cause.**
- [ ] **Step 3: Create a fresh Beget backup for each affected site.**
- [ ] **Step 4: Apply the smallest site-specific fix and preserve the original recipient.**
- [ ] **Step 5: Run PHP syntax checks and the focused regression check.**

### Task 3: Verify public behavior and delivery

**Files:**
- Create: `changes/2026-07-20/form-verification-results.json`
- Modify: `Финальный-отчет-проверки-2026-07-20.md`

**Interfaces:**
- Consumes: the post-fix live sites.
- Produces: fresh HTTP, form-response, recipient, and delivery evidence.

- [ ] **Step 1: Re-run the complete audit for all applicable domains.**
- [ ] **Step 2: Submit controlled technical test applications only where required to prove the fix.**
- [ ] **Step 3: Visually inspect every changed public form at desktop and mobile widths.**
- [ ] **Step 4: Record confirmed results, exclusions, and unresolved external dependencies.**

### Task 4: Client communication and repository completion

**Files:**
- Modify: `Финальный-отчет-проверки-2026-07-20.md`

**Interfaces:**
- Consumes: verified results from Task 3 and the latest Gmail threads.
- Produces: a concise client reply, pricing note for newly performed work, and a pushed repository commit.

- [ ] **Step 1: Calculate only newly performed work and avoid double billing prior fixes.**
- [ ] **Step 2: Reply in the existing client thread with completed domains, verified behavior, and any exact remaining dependency.**
- [ ] **Step 3: Run repository tests and the global harness smoke check.**
- [ ] **Step 4: Commit and push tracked reports, tests, and change artifacts without secrets.**
