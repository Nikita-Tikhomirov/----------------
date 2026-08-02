"""Classify incoming email against a reusable client profile."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TECHNICAL_KEYWORDS = (
    "проблем",
    "ошиб",
    "не работает",
    "бит",
    "сайт",
    "форм",
    "заявк",
    "кнопк",
    "правк",
    "доработ",
)

DEFAULT_MAIL_EVIDENCE_LEVELS = (
    "configured_recipient",
    "handler_acceptance",
    "smtp_mx_acceptance",
    "mailbox_receipt",
)


@dataclass(frozen=True)
class WorkflowPolicy:
    """Owner gates and recovery rules applied to every task for a client."""

    owner_approval_required: bool
    owner_release_required: bool
    client_contact_mode: str
    message_recovery_mode: str
    browser_fallback_scope: str
    mail_evidence_levels: tuple[str, ...]
    mailbox_receipt_required_for_delivery_claim: bool
    post_release_reverification_required: bool
    allow_finance_outreach: bool

    @classmethod
    def from_mapping(cls, value: Any) -> "WorkflowPolicy":
        if value is None:
            value = {}
        if not isinstance(value, dict):
            raise ValueError("profile field workflow must be an object")

        def boolean(name: str, default: bool) -> bool:
            result = value.get(name, default)
            if not isinstance(result, bool):
                raise ValueError(f"profile workflow field {name} must be boolean")
            return result

        contact_mode = value.get("client_contact_mode", "manual_owner_release_only")
        if contact_mode not in {"manual_owner_release_only", "autonomous"}:
            raise ValueError("profile workflow field client_contact_mode is invalid")

        recovery_mode = value.get("message_recovery_mode", "connector_then_main_chrome")
        if recovery_mode != "connector_then_main_chrome":
            raise ValueError("profile workflow field message_recovery_mode is invalid")

        browser_scope = value.get(
            "browser_fallback_scope",
            "main_chrome_only_no_hideo_9223",
        )
        if browser_scope != "main_chrome_only_no_hideo_9223":
            raise ValueError("profile workflow field browser_fallback_scope is invalid")

        raw_evidence_levels = value.get(
            "mail_evidence_levels",
            list(DEFAULT_MAIL_EVIDENCE_LEVELS),
        )
        if (
            not isinstance(raw_evidence_levels, list)
            or tuple(raw_evidence_levels) != DEFAULT_MAIL_EVIDENCE_LEVELS
        ):
            raise ValueError("profile workflow field mail_evidence_levels is invalid")

        return cls(
            owner_approval_required=boolean("owner_approval_required", True),
            owner_release_required=boolean("owner_release_required", True),
            client_contact_mode=contact_mode,
            message_recovery_mode=recovery_mode,
            browser_fallback_scope=browser_scope,
            mail_evidence_levels=tuple(raw_evidence_levels),
            mailbox_receipt_required_for_delivery_claim=boolean(
                "mailbox_receipt_required_for_delivery_claim",
                True,
            ),
            post_release_reverification_required=boolean(
                "post_release_reverification_required",
                True,
            ),
            allow_finance_outreach=boolean("allow_finance_outreach", False),
        )


@dataclass(frozen=True)
class ClientProfile:
    """Business identity and routing rules for one client."""

    id: str
    company_names: tuple[str, ...]
    contacts: tuple[str, ...]
    domains: tuple[str, ...]
    financial_keywords: tuple[str, ...]
    excluded_signals: tuple[str, ...]
    provider_domains: tuple[str, ...]
    provider_keywords: tuple[str, ...]
    mail_lookback_days: int
    mail_incremental_lookback_days: int
    workflow: WorkflowPolicy

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> "ClientProfile":
        def strings(name: str) -> tuple[str, ...]:
            raw = value.get(name, [])
            if not isinstance(raw, list) or not all(isinstance(item, str) and item.strip() for item in raw):
                raise ValueError(f"profile field {name} must be a list of non-empty strings")
            return tuple(item.casefold() for item in raw)

        identifier = value.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError("profile id must be a non-empty string")

        lookback_days = value.get("mail_lookback_days", 30)
        if not isinstance(lookback_days, int) or not 1 <= lookback_days <= 365:
            raise ValueError("profile field mail_lookback_days must be between 1 and 365")

        incremental_lookback_days = value.get("mail_incremental_lookback_days", 3)
        if not isinstance(incremental_lookback_days, int) or not 1 <= incremental_lookback_days <= lookback_days:
            raise ValueError(
                "profile field mail_incremental_lookback_days must be between 1 and mail_lookback_days"
            )

        return cls(
            id=identifier,
            company_names=strings("company_names"),
            contacts=strings("contacts"),
            domains=strings("domains"),
            financial_keywords=strings("financial_keywords"),
            excluded_signals=strings("excluded_signals"),
            provider_domains=strings("provider_domains"),
            provider_keywords=strings("provider_keywords"),
            mail_lookback_days=lookback_days,
            mail_incremental_lookback_days=incremental_lookback_days,
            workflow=WorkflowPolicy.from_mapping(value.get("workflow")),
        )

    @classmethod
    def from_json_file(cls, path: Path) -> "ClientProfile":
        return cls.from_mapping(json.loads(path.read_text(encoding="utf-8")))


@dataclass(frozen=True)
class RoutingDecision:
    bucket: str
    evidence: tuple[str, ...]
    requires_technical_task: bool


def build_search_queries(profile: ClientProfile, *, lookback_days: int | None = None) -> tuple[str, ...]:
    """Return Gmail queries that surface known and newly discovered client mail."""
    def grouped(values: tuple[str, ...]) -> str:
        return " OR ".join(f'"{value}"' for value in values)

    days = profile.mail_lookback_days if lookback_days is None else lookback_days
    if not 1 <= days <= profile.mail_lookback_days:
        raise ValueError("lookback_days must be between 1 and profile.mail_lookback_days")

    scope = f"in:inbox newer_than:{days}d"
    queries = [f"is:unread {scope}"]
    if profile.contacts:
        queries.append(f"{scope} ({grouped(profile.contacts)})")
    context = profile.company_names + profile.domains
    if context:
        queries.append(f"{scope} ({grouped(context)})")
    if profile.financial_keywords:
        queries.append(f"{scope} ({grouped(profile.financial_keywords)})")
    if profile.provider_domains:
        queries.append(f"{scope} ({grouped(profile.provider_domains)})")
    return tuple(queries)


def _message_text(message: dict[str, Any]) -> str:
    attachments = message.get("attachments", [])
    attachment_text = " ".join(item for item in attachments if isinstance(item, str))
    values = [message.get("from", ""), message.get("subject", ""), message.get("body", ""), attachment_text]
    return " ".join(value for value in values if isinstance(value, str)).casefold()


def _matches(text: str, values: tuple[str, ...], prefix: str) -> list[str]:
    return [f"{prefix}:{value}" for value in values if value in text]


def classify_message(profile: ClientProfile, message: dict[str, Any]) -> RoutingDecision:
    """Route a message using client context, not sender address alone."""
    text = _message_text(message)

    excluded = _matches(text, profile.excluded_signals, "excluded")
    if excluded:
        return RoutingDecision("unrelated", tuple(excluded), False)

    evidence = _matches(text, profile.contacts, "contact")
    evidence.extend(_matches(text, profile.company_names, "company"))
    evidence.extend(_matches(text, profile.domains, "domain"))
    finance = _matches(text, profile.financial_keywords, "financial")
    technical = _matches(text, TECHNICAL_KEYWORDS, "technical")
    provider = _matches(text, profile.provider_domains, "provider")
    provider_context = _matches(text, profile.provider_keywords, "provider_topic")

    if finance and evidence and technical:
        return RoutingDecision(
            "technical",
            tuple(evidence + technical + finance),
            True,
        )

    if finance and evidence:
        return RoutingDecision("finance", tuple(evidence + finance), False)

    if provider and (evidence or provider_context):
        return RoutingDecision("provider", tuple(evidence + provider + provider_context), True)

    if evidence:
        return RoutingDecision("technical", tuple(evidence), True)

    return RoutingDecision("unrelated", (), False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--message", type=Path)
    parser.add_argument("--search-plan", action="store_true")
    args = parser.parse_args()

    try:
        profile = ClientProfile.from_json_file(args.profile)
        if args.search_plan:
            print(json.dumps({"queries": build_search_queries(profile)}, ensure_ascii=False))
            return 0
        if args.message is None:
            raise ValueError("--message is required unless --search-plan is used")
        message = json.loads(args.message.read_text(encoding="utf-8"))
        if not isinstance(message, dict):
            raise ValueError("message must be a JSON object")
        decision = classify_message(profile, message)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Client message routing failed: {error}")
        return 2

    print(json.dumps(decision.__dict__, ensure_ascii=False, default=list))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
