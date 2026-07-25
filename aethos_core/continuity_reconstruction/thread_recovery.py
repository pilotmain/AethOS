# SPDX-License-Identifier: Apache-2.0
"""Thread recovery — reconstruct active operational thread with confidence ranking."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.continuity_reconstruction.ambiguity_scoring import score_continuity_ambiguity
from aethos_core.continuity_reconstruction.continuity_decay import apply_decay_to_confidence, compute_continuity_decay
from aethos_core.continuity_reconstruction.prompt_inference import infer_continuity_intent
from aethos_core.continuity_reconstruction.subject_affinity import select_primary_subject
from aethos_core.continuity_reconstruction.thread_isolation import score_thread_isolation
from aethos_core.operational_context_memory.context_bridge import build_operational_context_bridge
from aethos_core.operational_context_memory.cross_surface_bridge import merge_cross_surface_context
from aethos_core.operational_context_memory.memory_precedence import (
    apply_precedence_confidence_adjustment,
    reconcile_memory_layers,
)
from aethos_core.operational_thread_integrity.thread_integrity_runtime import assess_operational_thread_integrity
from aethos_core.conversation.realism.thread_resurrection_guard import assess_thread_resurrection


_CERTAINTY_THRESHOLD = 0.65
_LOW_CERTAINTY_THRESHOLD = 0.52


def _thread_age_hours(reconciliation: dict[str, Any]) -> float:
    for layer in reconciliation.get("layers") or []:
        ts = layer.get("updated_at") or layer.get("snapshot_at")
        if ts:
            return max(0.0, (time() - float(ts)) / 3600.0)
    return 0.0


def reconstruct_operational_thread(
    *,
    session_id: str = "default",
    channel: str = "chat",
    user_text: str = "",
) -> dict[str, Any]:
    bridge = build_operational_context_bridge(session_id=session_id, channel=channel)
    reconciliation = reconcile_memory_layers(session_id=session_id, channel=channel)
    try:
        from aethos_core.cross_surface_reality_convergence.convergence_runtime import orchestrate_cross_surface_convergence

        cross_surface = orchestrate_cross_surface_convergence(session_id=session_id, channel=channel)
    except Exception:
        cross_surface = merge_cross_surface_context(session_id=session_id)
    intent_info = infer_continuity_intent(user_text) if user_text else {"intent": None}

    if reconciliation.get("primary_subject"):
        bridge = {**bridge, "primary_subject": reconciliation["primary_subject"]}
    if reconciliation.get("investigations"):
        bridge = {**bridge, "active_investigations": reconciliation["investigations"]}

    selection = select_primary_subject(user_text=user_text or " ", bridge=bridge)
    ambiguity = score_continuity_ambiguity(
        user_text=user_text or " ",
        bridge=bridge,
        intent=intent_info.get("intent"),
    )
    isolation = score_thread_isolation(
        investigations=bridge.get("active_investigations") or [],
        focus_topics=bridge.get("focus_topics") or [],
        primary_subject=bridge.get("primary_subject"),
    )

    focus = selection.get("subject") or bridge.get("primary_subject") or "active operational thread"
    age_hours = _thread_age_hours(reconciliation)
    decay = compute_continuity_decay(age_hours=age_hours)

    confidence = float(bridge.get("continuity_confidence") or 0.5)
    confidence = apply_decay_to_confidence(base_confidence=confidence, age_hours=age_hours)
    confidence = apply_precedence_confidence_adjustment(base_confidence=confidence, reconciliation=reconciliation)

    if selection.get("confident"):
        confidence = min(0.95, confidence + 0.12)
    if ambiguity.get("ambiguous"):
        confidence = max(0.35, confidence - float(ambiguity.get("ambiguity_score") or 0.0) * 0.25)
    if isolation.get("conflated"):
        confidence = max(0.3, confidence - 0.1)
    if cross_surface.get("surfaces_aligned") and not cross_surface.get("drift_detected"):
        confidence = min(0.95, confidence + 0.08)
    elif cross_surface.get("drift_detected"):
        confidence = max(0.3, confidence - float(cross_surface.get("drift_score") or 0.0) * 0.2)
    if not reconciliation.get("reconciled"):
        confidence = max(0.3, confidence - 0.08)

    resurrection = assess_thread_resurrection(
        subject=str(selection.get("subject") or bridge.get("primary_subject") or ""),
        category=str(selection.get("category") or "recovery"),
        bridge=bridge,
        age_hours=age_hours,
    )
    if resurrection.get("resurrection_risk") or resurrection.get("confidence_penalty"):
        confidence = max(0.3, confidence - float(resurrection.get("confidence_penalty") or 0.0))

    certainty_tier = "high" if confidence >= _CERTAINTY_THRESHOLD else "moderate" if confidence >= _LOW_CERTAINTY_THRESHOLD else "low"
    integrity = assess_operational_thread_integrity(session_id=session_id, channel=channel, bridge=bridge)

    return {
        **bridge,
        "primary_subject": focus,
        "subject_selection": selection,
        "ambiguity": ambiguity,
        "thread_isolation": isolation,
        "continuity_decay": decay,
        "thread_resurrection": resurrection,
        "memory_reconciliation": reconciliation,
        "cross_surface": cross_surface,
        "thread_integrity": integrity,
        "continuity_confidence": round(confidence, 2),
        "certainty_tier": certainty_tier,
        "reconstructed": confidence >= _LOW_CERTAINTY_THRESHOLD and not (ambiguity.get("ambiguous") and certainty_tier == "low"),
        "infer_not_hallucinate": certainty_tier != "low" or ambiguity.get("ambiguous"),
        "summary": f"Reconstructed operational thread: {focus} ({certainty_tier} confidence, {decay.get('summary', 'decay evaluated')}).",
    }
