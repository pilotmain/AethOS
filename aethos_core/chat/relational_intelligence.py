# SPDX-License-Identifier: Apache-2.0
"""Relational intelligence chat lane — life, away, collaboration queries."""

from __future__ import annotations

import re

_RELATIONAL_RX = re.compile(
    r"\b(lifeos|life os|my calendar|my reminders|my goals|focus mode|"
    r"while you were away|collaboration session|start investigation|"
    r"how are you feeling|companion mode|mentor mode|operator mode)\b",
    re.I,
)


def is_relational_intelligence_request(text: str) -> bool:
    return bool(_RELATIONAL_RX.search(text or ""))


def execute_relational_intelligence(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_relational_intelligence_request(text):
        return None

    lower = text.lower()

    if "while you were away" in lower:
        from aethos_core.presence.ambient_presence import build_while_you_were_away

        away = build_while_you_were_away(session_id=session_id)
        body = f"**{away.get('title')}**\n\n{away.get('brief', '')}"
        return (
            body,
            "ambient_presence",
            {"lane": "relational_intelligence", "window_hours": str(away.get("window_hours", 8)), "autonomous_execution_blocked": "true"},
        )

    if "collaboration session" in lower or "start investigation" in lower:
        from aethos_core.collaboration.collaboration_runtime import start_collaboration_session

        focus = "deployment_debug" if "deploy" in lower else "investigation"
        collab = start_collaboration_session(operator_id=session_id, focus=focus, context=text[:200])
        sess = collab.get("session") or {}
        body = (
            f"Collaboration session started: `{sess.get('session_id')}`\n\n"
            f"Focus: **{sess.get('focus')}**\n\n"
            "Agents assist — you remain authoritative. Checkpoints require your validation."
        )
        return (
            body,
            "collaboration_session",
            {"lane": "relational_intelligence", "session_id": str(sess.get("session_id", "")), "autonomous_execution_blocked": "true"},
        )

    if any(k in lower for k in ("lifeos", "life os", "calendar", "reminders", "goals")):
        from aethos_core.life.life_runtime import get_lifeos_status, summarize_life_domain

        status = get_lifeos_status(session_id=session_id)
        if not status.get("opted_in"):
            body = (
                "LifeOS is **opt-in only** — personal operations remain explainable, revocable, and auditable.\n\n"
                "Say **opt in to lifeos** or enable from Mission Control → LifeOS."
            )
            return (body, "lifeos_opt_in", {"lane": "relational_intelligence", "autonomous_execution_blocked": "true"})

        domain = "calendar"
        for d in ("reminders", "goals", "focus", "travel", "learning"):
            if d in lower:
                domain = d
                break
        summary = summarize_life_domain(domain=domain, session_id=session_id)
        body = f"**LifeOS — {domain}**\n\n{summary.get('summary', '')}\n\nAll actions require your approval."
        return (body, "lifeos_domain", {"lane": "relational_intelligence", "domain": domain, "autonomous_execution_blocked": "true"})

    if any(k in lower for k in ("companion mode", "mentor mode", "operator mode", "executive mode", "crisis mode")):
        from aethos_core.relational.operator_style import set_operator_style

        mode = "companion"
        for m in ("mentor", "operator", "executive", "crisis", "coach"):
            if m in lower:
                mode = m
                break
        set_operator_style(session_id=session_id, preferred_mode=mode)
        body = f"Interaction mode set to **{mode}**. I'll adapt tone and verbosity accordingly."
        return (body, "operator_style", {"lane": "relational_intelligence", "mode": mode, "autonomous_execution_blocked": "true"})

    from aethos_core.relational.relational_runtime import get_relational_state

    state = get_relational_state(session_id=session_id)
    mode = (state.get("emotional_context") or {}).get("mode") or {}
    body = (
        f"Relational intelligence active — **{mode.get('mode', 'companion')}** mode.\n\n"
        f"{mode.get('reason', 'Calm operational partnership — steady, clear, and governed.')}"
    )
    return (body, "relational_state", {"lane": "relational_intelligence", "mode": str(mode.get("mode", "")), "autonomous_execution_blocked": "true"})
