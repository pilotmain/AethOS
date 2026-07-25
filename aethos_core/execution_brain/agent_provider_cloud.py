# SPDX-License-Identifier: Apache-2.0
"""Detect provider cloud conversation turns for agent-runtime delegation."""

from __future__ import annotations

import re

_PROVIDER_RX = None  # lazy — all Mission Control providers


def _provider_rx() -> re.Pattern[str]:
    global _PROVIDER_RX
    if _PROVIDER_RX is None:
        from aethos_core.execution_brain.cloud_provider_catalog import build_provider_name_pattern

        _PROVIDER_RX = build_provider_name_pattern()
    return _PROVIDER_RX
_CLOUD_OPS_RX = re.compile(
    r"\b("
    r"list|show|all|every|each|projects?|services?|apps?|inventory|"
    r"health|status|deployment|deployments?|logs?|restart|redeploy|"
    r"stop|pause|shutdown|inspect|check|verify|env|domains?|report\s+back|"
    # Credentialed devops verbs (handoff §4) — these must reach the agent runtime
    # + provider_exec, never a generic blurb or world-model responder.
    r"deploy|connect|wire|provision|migrate|rollback|set\s+up|setup|"
    r"create|fix|push|configure|rotate|seed|db\s+push"
    r")\b",
    re.I,
)
_MUTATION_RX = re.compile(
    r"\b(restart|redeploy|rollback|stop|pause|shutdown|set env|configure env|deploy|"
    r"connect|wire|provision|migrate|create|fix|db\s+push|push)\b",
    re.I,
)
_EXCLUDE_FIX_RX = re.compile(r"\bfix\s+\d+\b|\bpilot\s+\d+\b", re.I)
_MC_PROVIDER_RX = re.compile(
    r"\bmission\s+control\s+provider\s+inventory\b"
    r"|\b(?:list|show)\s+(?:all\s+)?(?:mission\s+control\s+)?providers?\b"
    r"|\b(?:all|every)\s+(?:mission\s+control\s+)?providers?\b"
    r"|\bscan\s+all\s+(?:mission\s+control\s+)?providers?\b"
    r"|\bquick\s+(?:mode|scan)\b"
    r"|\bfull\s+mode\b.*\bproviders?\b"
    r"|\bprovider\s+catalog\b",
    re.I,
)
_JOB_ARTIFACT_FOLLOWUP_RX = re.compile(
    r"\b("
    r"tell\s+me\b.*\b(?:here|in\s+chat)"
    r"|(?:here|in)\s+chat\s+please"
    r"|report\s+back"
    r"|health\s+status\s+here"
    r"|summar(?:y|ize).*(?:here|in\s+chat)"
    r"|show\s+(?:me\s+)?(?:the\s+)?(?:results?|report|summary)\s+(?:here|in\s+chat)"
    r"|what\s+did\s+(?:the|that)\s+job\s+(?:find|report|show)"
    r")\b",
    re.I,
)
_SERVICE_SLUG_RX = re.compile(r"\b[a-z0-9][a-z0-9._-]{2,}\b", re.I)
_COMMON_TARGET_WORDS = frozenset(
    {
        "here",
        "chat",
        "please",
        "status",
        "health",
        "check",
        "report",
        "back",
        "tell",
        "show",
        "run",
        "full",
        "operational",
        "picture",
        "deployment",
        "deployments",
        "logs",
        "inspect",
        "verify",
        "each",
        "every",
        "projects",
        "project",
        "services",
        "service",
        "vercel",
        "railway",
        "github",
        "latest",
        "recent",
        "governed",
    }
)


def is_agent_provider_cloud_request(text: str, *, session_id: str = "default") -> bool:
    """
    True when the turn should be handled by the agent tool loop,
    not legacy internal routers — inventory, health, logs, status, governed mutations.
    """
    raw = (text or "").strip()
    if len(raw) < 4 or _EXCLUDE_FIX_RX.search(raw):
        return False

    # A full provider inventory/scan is a deterministic provider-cloud intent and
    # must win over the multi-agent classifier (which otherwise claims "scan all
    # Mission Control providers" as coordination and starves the agent-cloud lane).
    if _MC_PROVIDER_RX.search(raw):
        return True

    from aethos_core.agents.runtime.planner import is_multi_agent_request

    if is_multi_agent_request(raw, session_id=session_id):
        return False

    if _is_pure_job_artifact_followup(raw):
        return False

    from aethos_core.provider_e2e_execution.provider_e2e_execution_intent import (
        is_provider_readonly_orchestration_intent,
    )

    if is_provider_readonly_orchestration_intent(raw):
        return True

    if _provider_rx().search(raw) and _CLOUD_OPS_RX.search(raw):
        return True

    if _session_has_provider_context(session_id) and _CLOUD_OPS_RX.search(raw):
        return True

    if _looks_like_named_service_target(raw) and _MUTATION_RX.search(raw):
        return True

    if _looks_like_named_service_target(raw) and re.search(r"\bhealth\b", raw, re.I):
        return True

    return False


def _is_pure_job_artifact_followup(text: str) -> bool:
    """Prior completed job surfaced in chat — not a fresh provider operation."""
    if not _JOB_ARTIFACT_FOLLOWUP_RX.search(text):
        return False
    if re.search(r"\b(restart|redeploy|rollback)\b", text, re.I):
        return False
    if re.search(r"\bhealth\s+check\b", text, re.I):
        return False
    if re.search(r"\b(check|verify|run)\b.*\bhealth\b", text, re.I):
        return False
    if _looks_like_named_service_target(text):
        return False
    return True


def _session_has_provider_context(session_id: str) -> bool:
    try:
        from aethos_core.operational_session.operational_session import load_operational_session

        session = load_operational_session(session_id=session_id)
        if session.has_active_subject():
            return True
        if session.subject.provider or session.subject.vercel_project or session.subject.project:
            return True
        if session.context.last_operation:
            return True
    except Exception:
        return False
    return False


def _looks_like_named_service_target(text: str) -> bool:
    """Project/service slug without explicit provider (e.g. influencer-crm)."""
    if not re.search(
        r"\b(restart|redeploy|health|logs|status|deployment|check|inspect)\b",
        text,
        re.I,
    ):
        return False
    for match in _SERVICE_SLUG_RX.finditer(text):
        token = match.group(0).lower()
        if token in _COMMON_TARGET_WORDS:
            continue
        if any(ch in token for ch in "-_."):
            return True
        if len(token) >= 5:
            return True
    return False
