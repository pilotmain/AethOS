# SPDX-License-Identifier: Apache-2.0
"""Grounding runtime — orchestration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.continuity_reconstruction.prompt_inference import infer_continuity_intent
from aethos_core.continuity_reconstruction.thread_recovery import reconstruct_operational_thread
from aethos_core.conversation.realism.realism_runtime import assess_conversational_realism
from aethos_core.governance_restraint_runtime.restraint_runtime import assess_governance_restraint
from aethos_core.operational_context_memory.context_bridge import build_operational_context_bridge
from aethos_core.operational_partner_presence.partner_runtime import build_partner_context
from aethos_core.telegram_session_persistence.session_bridge import hydrate_telegram_session


def orchestrate_operational_grounding(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    bridge = build_operational_context_bridge(session_id=session_id, channel=channel)
    thread = reconstruct_operational_thread(session_id=session_id, channel=channel)
    partner = build_partner_context(session_id=session_id, channel=channel)
    telegram = hydrate_telegram_session(session_id=session_id)
    governance = assess_governance_restraint(channel=channel, grounded=True)
    realism = assess_conversational_realism()
    grounded = bridge.get("has_memory") and thread.get("reconstructed")
    return {
        "operational_context": bridge,
        "continuity_thread": thread,
        "partner_presence": partner,
        "telegram_persistence": telegram,
        "governance_restraint": governance,
        "conversational_realism": realism,
        "grounded": grounded or partner.get("investigation_aware"),
        "summary": "Conversational operational grounding active — continuity and runtime truth injected.",
    }


def prepare_grounding_context(
    *,
    user_text: str,
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    intent_info = infer_continuity_intent(user_text)
    grounding = orchestrate_operational_grounding(session_id=session_id, channel=channel)
    grounding["continuity_intent"] = intent_info
    grounding["session_id"] = session_id
    grounding["channel"] = channel
    return grounding
