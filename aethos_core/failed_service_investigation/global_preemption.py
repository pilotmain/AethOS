# SPDX-License-Identifier: Apache-2.0
"""Global preemption for cached failed/unknown Railway services."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

from aethos_core.failed_service_investigation.failed_service_memory import (
    get_health_report_meta,
    get_preemptible_health_rows,
)
from aethos_core.failed_service_investigation.failed_service_resolver import (
    InvestigationKind,
    _match_rows,
    resolve_failed_service_target,
    row_key,
)

FailedServiceIntent = Literal[
    "why_failed",
    "show_logs",
    "show_error_logs",
    "inspect_events",
    "create_fix_plan",
    "what_should_i_fix",
    "retry_check",
    "status",
    "none",
]

_OPERATIONAL_CUE_RX = re.compile(
    r"\b("
    r"fail(?:ed|ing|ure)?|down|crash(?:ed|ing)?|broken|unhealthy|error|"
    r"logs?|events?|fix|diagnos|inspect|investigate|debug|analyze|"
    r"status|retry|re-?check|why|what(?:'s|\s+is)|how\s+to"
    r")\b",
    re.I,
)

# Credential/connection status across providers is NOT a failed-service investigation — it's
# a Connections/credentials query. Without this guard, "connection status for all providers"
# gets claimed by the failed-service lane and returns a bogus "couldn't match to a service".
_CONNECTIONS_STATUS_RX = re.compile(
    r"\bconnection(?:s)?\s+(?:status|state|health)\b"
    r"|\b(?:status|state)\s+(?:of|for)\s+(?:all\s+|my\s+)*(?:provider|connection)s?\b"
    r"|\b(?:show|list|check|validate)\s+(?:my\s+|all\s+)*(?:provider\s+)?connections?\b"
    r"|\b(?:connection|credential)s?\s+for\s+all\s+providers?\b",
    re.I,
)


def _is_connections_status_query(text: str) -> bool:
    return bool(_CONNECTIONS_STATUS_RX.search(text or ""))

_WHY_FAILED_RX = re.compile(
    r"\bwhy\s+(?:is|are|did|was)\s+(.+?)\s+(?:fail(?:ed|ing)?|down|crashed|broken)\b",
    re.I,
)
_WHY_FAILED_SHORT_RX = re.compile(r"\bwhy\s+(?:is|did)\s+(.+?)\s+fail\b", re.I)
_FIX_PLAN_RX = re.compile(
    r"\b(?:create|make|build|draft|give\s+me\s+(?:a\s+)?)?fix\s+plan\s+(?:for\s+)?(.+?)\s*$",
    re.I,
)
_WHAT_FIX_RX = re.compile(
    r"\b(?:what\s+should\s+i\s+fix|how\s+(?:do\s+i|to)\s+fix|what\s+(?:needs|to)\s+(?:to\s+)?be\s+fixed)\b",
    re.I,
)
_LOGS_RX = re.compile(
    r"\b(?:check|show|fetch|get|read|tail)\s+(?:the\s+)?(?:.+?\s+)?logs?\s*(?:for\s+(.+?))?\s*$",
    re.I,
)
_ERROR_LOGS_RX = re.compile(
    r"\b(?:check|show|fetch|get|read|tail)\s+(?:the\s+)?(.+?\s+)?error\s+logs?\b",
    re.I,
)
_INSPECT_EVENTS_RX = re.compile(
    r"\b(?:inspect|check|show|fetch|get|list|read)\s+(?:the\s+)?(.+?\s+)?(?:service\s+)?events?\b",
    re.I,
)
_INVESTIGATION_RX = re.compile(
    r"\b(?:diagnose|investigate|debug|analyze)\s+(?:the\s+)?(.+?)(?:\s+failure|\s+service)?\s*$",
    re.I,
)
_STATUS_RX = re.compile(
    r"\b(?:(?:what(?:'s|\s+is)\s+(?:the\s+)?status(?:\s+(?:of|for))?)|status\s+(?:of|for))\s+(.+?)\s*$",
    re.I,
)
_RETRY_RX = re.compile(r"\b(?:retry|try\s+again|re-?check)\b.*\b(.+?)\s*$", re.I)


@dataclass
class FailedServiceReference:
    rows: list[dict[str, Any]]
    match_reason: str = "referenced cached failed/unknown service"


def classify_failed_service_intent(text: str) -> FailedServiceIntent:
    raw = (text or "").strip()
    if not raw:
        return "none"
    if _FIX_PLAN_RX.search(raw):
        return "create_fix_plan"
    if _WHAT_FIX_RX.search(raw):
        return "what_should_i_fix"
    if _INSPECT_EVENTS_RX.search(raw):
        return "inspect_events"
    if _ERROR_LOGS_RX.search(raw):
        return "show_error_logs"
    if _LOGS_RX.search(raw):
        return "show_logs"
    if _WHY_FAILED_RX.search(raw) or _WHY_FAILED_SHORT_RX.search(raw):
        return "why_failed"
    if _INVESTIGATION_RX.search(raw):
        return "why_failed"
    if _STATUS_RX.search(raw):
        return "status"
    if _RETRY_RX.search(raw):
        return "retry_check"
    return "none"


def _intent_to_kind(intent: FailedServiceIntent) -> InvestigationKind:
    mapping: dict[str, InvestigationKind] = {
        "why_failed": "why_failed",
        "show_logs": "check_logs",
        "show_error_logs": "check_logs",
        "inspect_events": "inspect_events",
        "create_fix_plan": "fix_plan",
        "what_should_i_fix": "fix_plan",
        "retry_check": "why_failed",
        "status": "status",
    }
    return mapping.get(intent, "none")  # type: ignore[return-value]


def detect_failed_service_reference(text: str, *, session_id: str = "default", provider: str = "railway") -> FailedServiceReference | None:
    rows = get_preemptible_health_rows(session_id=session_id, provider=provider)
    if not rows:
        return None
    matches = [row for row in rows if _row_referenced_in_text(row, text)]
    if not matches:
        matches = _match_rows(rows, _extract_reference_phrase(text), text)
    if not matches:
        return None
    unique = {row_key(row): row for row in matches}
    return FailedServiceReference(rows=list(unique.values()), match_reason="matched cached failed/unknown service row")


def _extract_reference_phrase(text: str) -> str:
    intent = classify_failed_service_intent(text)
    if intent != "none":
        from aethos_core.failed_service_investigation.failed_service_resolver import _extract_phrase

        return _extract_phrase(text, _intent_to_kind(intent))
    return text or ""


def _row_referenced_in_text(row: dict[str, Any], text: str) -> bool:
    raw_norm = re.sub(r"[\s_\-]+", " ", (text or "").strip().lower())
    service = str(row.get("service") or "")
    project = str(row.get("project") or "")
    service_id = str(row.get("service_id") or "")
    combined = f"{project}/{service}".strip("/")
    for candidate in (service, project, service_id, combined):
        token = re.sub(r"[\s_\-]+", " ", candidate.strip().lower())
        if len(token) < 3:
            continue
        if token in raw_norm:
            return True
        if token.replace(" ", "-") in (text or "").lower():
            return True
        for part in token.split():
            if len(part) >= 4 and part in raw_norm:
                return True
    return False


def should_preempt_to_failed_service(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.chat.route_trace import is_internal_diagnostics_query
    from aethos_core.operational_target_resolution.explicit_target_resolver import (
        explicit_target_overrides_session_context,
        resolve_explicit_operational_target,
        should_route_explicit_provider_diagnostics,
    )

    if _is_connections_status_query(text):
        return False
    if should_route_explicit_provider_diagnostics(text, session_id=session_id):
        return False
    if explicit_target_overrides_session_context(text, session_id=session_id):
        return False

    explicit = resolve_explicit_operational_target(text)
    if explicit is not None and explicit.provider in {"vercel", "github"} and explicit.has_diagnostic_intent:
        return False

    if is_internal_diagnostics_query(text):
        return False

    from aethos_core.world_model.world_model_followup_router import is_world_model_followup

    if is_world_model_followup(text, session_id=session_id):
        return True

    intent = classify_failed_service_intent(text)
    if intent == "none" and not is_cognition_owned_failure_investigation(text, session_id=session_id):
        return False
    if get_health_report_meta(session_id=session_id).get("has_report"):
        if detect_failed_service_reference(text, session_id=session_id) is None:
            return bool(_OPERATIONAL_CUE_RX.search(text or "")) or is_cognition_owned_failure_investigation(
                text, session_id=session_id
            )
        return True
    return is_cognition_owned_failure_investigation(text, session_id=session_id)


def is_cognition_owned_failure_investigation(text: str, *, session_id: str = "default") -> bool:
    """Failure diagnostics belong to cognition unless the user explicitly scoped another provider."""
    from aethos_core.chat.route_trace import is_internal_diagnostics_query

    if is_internal_diagnostics_query(text):
        return False

    intent = classify_failed_service_intent(text)
    if intent != "none":
        raw = (text or "").lower()
        if re.search(r"\bvercel\b", raw) and not re.search(r"\brailway\b", raw):
            return False
        if re.search(r"\bgithub\b", raw) and not re.search(r"\brailway\b", raw):
            if intent in {"inspect_events", "show_logs", "show_error_logs"}:
                return False
        return True

    from aethos_core.operations.intents import matches_vercel_failure_diagnostic

    raw = (text or "").lower()
    if matches_vercel_failure_diagnostic(text) and not re.search(r"\bvercel\b", raw):
        return True
    return False


def should_block_generic_diagnostics(text: str, *, session_id: str = "default") -> bool:
    """Block Vercel/browser/generic paths when a cached failed/unknown row is referenced."""
    return should_preempt_to_failed_service(text, session_id=session_id)


def route_failed_service_intent(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not should_preempt_to_failed_service(text, session_id=session_id):
        return None

    from aethos_core.failed_service_investigation.failed_service_router import compose_failed_service_investigation_reply

    return compose_failed_service_investigation_reply(text, session_id=session_id)
