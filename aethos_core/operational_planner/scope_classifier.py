# SPDX-License-Identifier: Apache-2.0
"""Operational scope classification — active thread is context, not prison."""

from __future__ import annotations

import re
from typing import Literal

ScopeType = Literal[
    "active_target",
    "provider_service",
    "provider_wide",
    "all_providers",
    "workspace_wide",
    "unknown",
]

_EXPLICIT_PROVIDER_RX = re.compile(r"\b(railway|vercel|github|docker|kubernetes|aws|k8s)\b", re.I)

_PROVIDER_WIDE_RX = re.compile(
    r"\b("
    r"(?:all|every|each)\s+(?:the\s+)?(?:available\s+)?(?:services?|apps?|projects?|deployments?)"
    r"|(?:services?|apps?|projects?|deployments?)\s+(?:that\s+are\s+)?(?:all|every|each)"
    r"|(?:all|every)\s+(?:available\s+)?(?:services?|apps?)\s+(?:in|on|across)\s+(?:railway|vercel|github|aws|docker|kubernetes)"
    r"|(?:check|list|show|report(?:\s+back)?(?:\s+on|\s+with)?)\s+(?:all|every)\b"
    r"|(?:all|every)\b.*\b(?:available|running|healthy|failed|unhealthy|down)\b"
    r"|provider[- ]wide"
    r"|across\s+(?:all\s+)?(?:my\s+)?(?:services?|projects?|apps?)"
    r"|every\s+service\s+(?:in|on)\s+(?:railway|vercel|github|aws)"
    r")\b",
    re.I,
)

_ALL_PROVIDERS_RX = re.compile(
    r"\b(all|every)\s+(?:providers?|clouds?|platforms?)\b|\bacross\s+all\s+providers\b",
    re.I,
)

_WORKSPACE_WIDE_RX = re.compile(
    r"\b(entire|whole)\s+(?:workspace|infrastructure|stack)\b|\beverything\s+(?:in|on)\s+(?:my\s+)?(?:stack|infra)\b",
    re.I,
)

_SINGLE_SERVICE_MUTATION_RX = re.compile(
    r"\b(restart|redeploy|deploy|rollback|scale|stop|start)\b.{0,40}\b([a-z0-9][a-z0-9-]{1,62})\b",
    re.I,
)


def explicit_provider_in_prompt(text: str) -> str | None:
    match = _EXPLICIT_PROVIDER_RX.search(text or "")
    if not match:
        return None
    provider = match.group(1).lower()
    return "kubernetes" if provider == "k8s" else provider


def is_provider_wide_phrase(text: str) -> bool:
    raw = text or ""
    if _PROVIDER_WIDE_RX.search(raw):
        return True
    if re.search(r"\b(all|every)\b", raw, re.I) and re.search(r"\b(services?|apps?|projects?)\b", raw, re.I):
        return True
    if re.search(r"\b(failed|unhealthy|down)\s+services?\b", raw, re.I) and not _SINGLE_SERVICE_MUTATION_RX.search(raw):
        return True
    return False


def classify_operational_scope(text: str, *, session_id: str = "default") -> ScopeType:
    raw = (text or "").strip()
    if not raw:
        return "unknown"

    if _WORKSPACE_WIDE_RX.search(raw):
        return "workspace_wide"
    if _ALL_PROVIDERS_RX.search(raw):
        return "all_providers"
    if is_provider_wide_phrase(raw):
        return "provider_wide"

    if _SINGLE_SERVICE_MUTATION_RX.search(raw) or re.search(
        r"\b(restart|redeploy|deploy)\b.{0,20}\b[a-z0-9][a-z0-9-]{1,62}\b", raw, re.I
    ):
        return "provider_service"

    from aethos_core.conversation.provider_memory.active_provider_context import is_provider_neutral_health_phrase

    if is_provider_neutral_health_phrase(raw, session_id=session_id):
        from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

        if get_active_operational_thread(session_id) is not None:
            return "active_target"

    from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

    thread = get_active_operational_thread(session_id)
    if thread is not None and not explicit_provider_in_prompt(raw):
        from aethos_core.conversation.provider_memory.followup_intent_classifier import classify_followup_intent

        if classify_followup_intent(raw, thread) is not None:
            return "active_target"

    if explicit_provider_in_prompt(raw):
        return "provider_service"

    return "unknown"
