# SPDX-License-Identifier: Apache-2.0
"""Living intelligence chat lane — conversation, copilot, live presence."""

from __future__ import annotations

import re

_LIVING_RX = re.compile(
    r"\b(continue where we left off|pick up where|resume conversation|"
    r"copilot|co-pilot|root cause|hypothesis|why did this fail|"
    r"live presence|what am i working on|nudge me|help me debug|"
    r"collaboration room|team investigation)\b",
    re.I,
)


def is_living_intelligence_request(text: str) -> bool:
    return bool(_LIVING_RX.search(text or ""))


def execute_living_intelligence(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_living_intelligence_request(text):
        return None

    lower = text.lower()

    if "continue where" in lower or "pick up where" in lower or "resume conversation" in lower:
        from aethos_core.conversation.operational_memory import persist_investigation, record_focus_recovery
        from aethos_core.human_centered.continuity_memory import record_manual_validation_request
        from aethos_core.human_centered.operational_partner_runtime import render_operational_partner_brief
        record_focus_recovery(session_id=session_id, focus="conversation continuity", channel=channel)
        persist_investigation(session_id=session_id, investigation="conversation resume")
        record_manual_validation_request(session_id=session_id, request=text[:200])
        resume = render_operational_partner_brief(session_id=session_id, user_text=text)
        return (
            resume.get("brief", "No prior context found."),
            "conversation_resume",
            {
                "lane": "living_intelligence",
                "confidence": str(resume.get("confidence", 0.82)),
                "calm_intelligence": "true",
                "operational_depth": "true",
                "autonomous_execution_blocked": "true",
            },
        )

    if "copilot" in lower or "co-pilot" in lower or "hypothesis" in lower or "root cause" in lower or "why did this fail" in lower:
        from aethos_core.copilot.copilot_runtime import build_copilot_brief

        body = build_copilot_brief(session_id=session_id, user_text=text)
        return (
            body,
            "operational_copilot",
            {"lane": "living_intelligence", "autonomous_execution_blocked": "true"},
        )

    if "live presence" in lower or "what am i working on" in lower or "nudge" in lower:
        from aethos_core.human_centered.operational_partner_runtime import render_operational_partner_brief
        from aethos_core.presence.live.live_presence_runtime import record_focus

        if "deploy" in lower or "railway" in lower:
            record_focus(session_id=session_id, topic="Railway deployment debugging")
        elif "workflow" in lower:
            record_focus(session_id=session_id, topic="GitHub workflow investigation")
        brief = render_operational_partner_brief(session_id=session_id, user_text=text)
        timing = (brief.get("attention_awareness") or {})
        if timing.get("fatigue_level") == "high" and not timing.get("should_interrupt", True):
            body = timing.get("narrative", "I'll summarize when you're ready.") + "\n\n*(Focus protection active — calm mode.)*"
        else:
            body = brief.get("brief", "Live presence active.")
        return (
            body,
            "live_presence_nudge",
            {"lane": "living_intelligence", "calm_intelligence": "true", "operational_depth": "true", "autonomous_execution_blocked": "true"},
        )

    if "collaboration room" in lower or "team investigation" in lower:
        from aethos_core.collaboration.teamwork_runtime import create_collaboration_room

        room = create_collaboration_room(operator_id=session_id, title=text[:80], focus="investigation")
        r = room.get("room") or {}
        body = (
            f"Collaboration room opened: `{r.get('room_id')}`\n\n"
            f"**{r.get('title')}** — shared evidence board ready.\n\n"
            "Agents assist. You remain authoritative."
        )
        return (
            body,
            "teamwork_room",
            {"lane": "living_intelligence", "room_id": str(r.get("room_id", "")), "autonomous_execution_blocked": "true"},
        )

    from aethos_core.human_centered.living_companion_runtime import get_living_companion_overview

    overview = get_living_companion_overview(session_id=session_id)
    body = (
        "**Living Intelligence Active**\n\n"
        f"Phase {overview.get('phase')} — {overview.get('identity')}\n\n"
        "Try: *continue where we left off*, *copilot analysis*, *nudge me*, or *open collaboration room*."
    )
    return (
        body,
        "living_intelligence",
        {"lane": "living_intelligence", "autonomous_execution_blocked": "true"},
    )
