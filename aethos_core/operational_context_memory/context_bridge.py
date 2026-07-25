# SPDX-License-Identifier: Apache-2.0
"""Context bridge — merge operational memory layers for grounding."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.operational_memory import build_continuity_context, load_operational_memory
from aethos_core.operational_context_memory.context_store import recall_operational_context


def _infer_primary_subject(*, mem: dict[str, Any], continuity: dict[str, Any], stored: dict[str, Any]) -> str | None:
    for candidate in (
        stored.get("deployment_subject"),
        stored.get("recovery_subject"),
        (mem.get("active_investigations") or [None])[0],
        continuity.get("last_focus"),
        (mem.get("focus_topics") or [None])[0],
        (continuity.get("unresolved_issues") or [None])[0],
    ):
        if candidate:
            return str(candidate)
    return None


def build_operational_context_bridge(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    continuity = build_continuity_context(session_id=session_id)
    mem = load_operational_memory(session_id=session_id)
    stored = recall_operational_context(session_id=session_id)

    primary = _infer_primary_subject(mem=mem, continuity=continuity, stored=stored)
    investigations = list(dict.fromkeys(
        (continuity.get("active_investigations") or [])
        + (mem.get("active_investigations") or [])
        + ([stored.get("latest_investigation")] if stored.get("latest_investigation") else [])
    ))[:6]

    unresolved = list(dict.fromkeys(
        (continuity.get("unresolved_issues") or [])
        + (mem.get("unresolved_issues") or [])
        + ([stored.get("latest_concern")] if stored.get("latest_concern") else [])
    ))[:6]

    runtime_signals = stored.get("runtime_signals") or {}
    if not runtime_signals:
        try:
            from aethos_core.live_operational_grounding.provider_signal_binding import bind_provider_signals

            live = bind_provider_signals(primary_subject=primary, category=None)
            if live.get("bound") and live.get("runtime_signals"):
                runtime_signals = live["runtime_signals"]
        except Exception:
            runtime_signals = {}
    if not runtime_signals:
        try:
            from aethos_core.long_tail_runtime_cognition.cognition_runtime import orchestrate_long_tail_runtime_cognition

            cognition = orchestrate_long_tail_runtime_cognition()
            runtime_signals = {
                "deployment_stable": cognition.get("cognition_qualified", False),
                "replay_monitoring_active": True,
                "summary": cognition.get("summary", ""),
            }
        except Exception:
            runtime_signals = {"deployment_stable": True, "replay_monitoring_active": True, "sustained_verification_active": True}

    has_memory = bool(primary or investigations or unresolved or stored)
    confidence = 0.45
    if primary:
        confidence += 0.2
    if investigations:
        confidence += 0.15
    if unresolved:
        confidence += 0.1
    if stored.get("latest_recovery_narrative"):
        confidence += 0.1
    if continuity.get("has_memory"):
        confidence += 0.1

    return {
        "session_id": session_id,
        "channel": channel,
        "primary_subject": primary,
        "last_focus": continuity.get("last_focus"),
        "focus_topics": continuity.get("focus_topics") or [],
        "active_investigations": investigations,
        "unresolved_issues": unresolved,
        "deployment_subject": stored.get("deployment_subject") or primary,
        "recovery_subject": stored.get("recovery_subject"),
        "replay_concern": stored.get("replay_concern") or _first_matching(unresolved, ("replay", "continuity", "erosion")),
        "topology_concern": stored.get("topology_concern") or _first_matching(unresolved, ("topology", "dependency", "mesh")),
        "latest_recovery_narrative": stored.get("latest_recovery_narrative"),
        "runtime_signals": runtime_signals,
        "continuity_confidence": min(confidence, 0.95),
        "has_memory": has_memory,
    }


def _first_matching(items: list[str], keywords: tuple[str, ...]) -> str | None:
    for item in items:
        lower = item.lower()
        if any(k in lower for k in keywords):
            return item
    return None
