# SPDX-License-Identifier: Apache-2.0
"""Operational entity chat integration."""

from __future__ import annotations

from aethos_core.agents.runtime.execution_runtime import orchestrate_operational_entity


def try_operational_entity_reply(
    user_text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> tuple[str, str, dict[str, str]] | None:
    result = orchestrate_operational_entity(user_text=user_text, session_id=session_id, channel=channel)
    if result is None:
        return None
    meta = {
        "lane": str(result.get("lane") or "operational_entity"),
        "grounded": "true",
        "execution_qualified": str(result.get("execution_qualified", True)),
        "entity_count": str((result.get("continuity") or {}).get("entity_count") or 0),
    }
    return result["reply"], str(result.get("intent") or "operational_entity"), meta


def try_operational_continuity_guard(
    user_text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> tuple[str, str, dict[str, str]] | None:
    """Prevent LLM fallback collapse when an operational workspace is active."""
    from aethos_core.conversation.progression_inference import infer_operational_continuity_intercept
    from aethos_core.conversation.progression_compat import compose_continuity_fallback_reply
    from aethos_core.operational_entity_runtime.lightweight_agent_registry import list_active_entities

    if not list_active_entities(session_id=session_id):
        return None
    if not infer_operational_continuity_intercept(user_text).get("intercept"):
        return None
    handled = try_operational_entity_reply(user_text, session_id=session_id, channel=channel)
    if handled is not None:
        return handled
    body = compose_continuity_fallback_reply(session_id=session_id, user_text=user_text)
    if not body:
        return None
    meta = {"lane": "operational_progression", "grounded": "true", "execution_qualified": "true"}
    return body, "operational_continuity", meta


def enrich_operational_entity_context(emotional_context: dict, *, session_id: str, channel: str) -> dict:
    from aethos_core.agent_continuity_memory.continuity_store import build_agent_continuity_context

    emotional_context["operational_entity"] = build_agent_continuity_context(session_id=session_id)
    emotional_context["session_id"] = session_id
    emotional_context["channel"] = channel
    return emotional_context
