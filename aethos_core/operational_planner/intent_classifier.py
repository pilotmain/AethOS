# SPDX-License-Identifier: Apache-2.0
"""Operational intent classification."""

from __future__ import annotations

import re
from typing import Literal

IntentType = Literal[
    "inventory_health_report",
    "inventory_list",
    "health_check",
    "verify_operation",
    "fetch_logs",
    "mutation",
    "discovery",
    "unknown",
]

_INVENTORY_HEALTH_RX = re.compile(
    r"\b("
    r"(?:all|every)\s+(?:the\s+)?(?:services?|apps?|projects?)"
    r"|(?:services?|apps?)\s+(?:that\s+are\s+)?(?:running|healthy|failed|unhealthy|down)"
    r"|(?:running|healthy|failed|unhealthy)\s+(?:with\s+)?(?:the\s+)?service\s+names?"
    r"|report\s+back\s+with\s+(?:running|healthy|failed)"
    r"|overall\s+(?:health|status)"
    r"|health\s+(?:report|summary|overview)"
    r")\b",
    re.I,
)

_INVENTORY_LIST_RX = re.compile(
    r"\b(list|show|what are)\b.*\b(services?|apps?|projects?)\b",
    re.I,
)

_MUTATION_RX = re.compile(r"\b(restart|redeploy|deploy|rollback|scale|stop|start|delete)\b", re.I)


def classify_operational_intent(text: str, *, scope: str = "unknown", session_id: str = "default") -> IntentType:
    raw = (text or "").strip()
    if not raw:
        return "unknown"

    if scope in {"provider_wide", "all_providers", "workspace_wide"}:
        if _INVENTORY_HEALTH_RX.search(raw) or re.search(r"\b(healthy|failed|running|unhealthy|down)\b", raw, re.I):
            return "inventory_health_report"
        if _INVENTORY_LIST_RX.search(raw) or re.search(r"\b(all|every)\b.*\b(services?|apps?)\b", raw, re.I):
            return "inventory_list"
        return "inventory_health_report"

    if _MUTATION_RX.search(raw):
        return "mutation"

    from aethos_core.conversation.provider_memory.active_provider_context import is_provider_neutral_health_phrase

    if is_provider_neutral_health_phrase(raw, session_id=session_id):
        from aethos_core.post_mutation_verification.verification_intent_router import (
            is_post_mutation_verification_intent,
            recent_mutation_lifecycle_exists,
        )

        if recent_mutation_lifecycle_exists(session_id=session_id) and is_post_mutation_verification_intent(
            raw, session_id=session_id
        ):
            return "verify_operation"
        return "health_check"

    from aethos_core.conversation.provider_memory.followup_intent_classifier import classify_followup_intent

    if scope == "active_target":
        from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

        thread = get_active_operational_thread(session_id)
        if thread is not None:
            intent = classify_followup_intent(raw, thread)
            if intent is not None:
                mapping = {
                    "health_check": "health_check",
                    "verify_operation": "verify_operation",
                    "fetch_logs": "fetch_logs",
                    "fetch_top_n_logs": "fetch_logs",
                    "get_status": "health_check",
                }
                return mapping.get(intent.intent, "unknown")  # type: ignore[return-value]

    if _INVENTORY_LIST_RX.search(raw):
        return "inventory_list"

    return "unknown"
