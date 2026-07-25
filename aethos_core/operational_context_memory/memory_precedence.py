# SPDX-License-Identifier: Apache-2.0
"""Memory precedence — hierarchy, reconciliation, and source authority."""

from __future__ import annotations

from time import time
from typing import Any

# Higher rank = stronger authority for conversational grounding.
_SOURCE_RANK: dict[str, int] = {
    "live_operational_grounding": 95,
    "active_investigation": 100,
    "runtime_truth": 90,
    "operational_context_store": 80,
    "operational_memory": 70,
    "human_continuity": 60,
    "relational_recent": 50,
    "inferred": 30,
}


def reconcile_memory_layers(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    """Merge memory layers with precedence rules — resolve contradictions by authority."""
    layers: list[dict[str, Any]] = []

    try:
        from aethos_core.conversation.operational_memory import build_continuity_context

        continuity = build_continuity_context(session_id=session_id)
        if continuity.get("has_memory"):
            layers.append({
                "source": "operational_memory",
                "rank": _SOURCE_RANK["operational_memory"],
                "primary_subject": continuity.get("last_focus"),
                "investigations": continuity.get("active_investigations") or [],
                "unresolved": continuity.get("unresolved_issues") or [],
            })
    except Exception:
        pass

    try:
        from aethos_core.operational_context_memory.context_store import recall_operational_context

        stored = recall_operational_context(session_id=session_id)
        if stored:
            layers.append({
                "source": "operational_context_store",
                "rank": _SOURCE_RANK["operational_context_store"],
                "primary_subject": stored.get("deployment_subject") or stored.get("latest_focus"),
                "investigations": [stored["latest_investigation"]] if stored.get("latest_investigation") else [],
                "updated_at": stored.get("updated_at"),
            })
    except Exception:
        pass

    try:
        from aethos_core.operational_context_memory.investigation_lifecycle import load_investigation_threads

        threads = load_investigation_threads(session_id=session_id)
        active = [t for t in threads if t.get("status") == "active"]
        if active:
            layers.append({
                "source": "active_investigation",
                "rank": _SOURCE_RANK["active_investigation"],
                "primary_subject": active[0].get("investigation"),
                "investigations": [t.get("investigation") for t in active if t.get("investigation")],
                "snapshot_at": active[0].get("snapshot_at"),
            })
    except Exception:
        pass

    try:
        from aethos_core.human_centered.continuity_memory import load_continuity_memory

        hc = load_continuity_memory(session_id=session_id)
        if hc.get("focus"):
            layers.append({
                "source": "human_continuity",
                "rank": _SOURCE_RANK["human_continuity"],
                "primary_subject": hc.get("focus") or hc.get("current_system_focus"),
                "unresolved": hc.get("unresolved") or [],
            })
    except Exception:
        pass

    try:
        from aethos_core.cross_surface_reality_convergence.runtime_truth_binding import bind_runtime_truth

        truth = bind_runtime_truth(primary_subject=layers[0].get("primary_subject") if layers else None)
        if truth.get("runtime_truth_bound"):
            layers.append({
                "source": "runtime_truth",
                "rank": _SOURCE_RANK["runtime_truth"],
                "primary_subject": truth.get("truth_subject"),
                "converged": truth.get("truth_converged"),
            })
    except Exception:
        pass

    layers.sort(key=lambda l: l.get("rank", 0), reverse=True)
    authoritative = layers[0] if layers else {}

    contradictions: list[str] = []
    if len(layers) >= 2:
        subjects = {l.get("primary_subject") for l in layers if l.get("primary_subject")}
        if len(subjects) > 1:
            contradictions.append("competing_primary_subjects")

    reconciled_subject = authoritative.get("primary_subject")
    investigations: list[str] = []
    for layer in layers:
        investigations.extend(layer.get("investigations") or [])
    investigations = list(dict.fromkeys(investigations))[:8]

    return {
        "layers": layers,
        "authoritative_source": authoritative.get("source"),
        "primary_subject": reconciled_subject,
        "investigations": investigations,
        "contradictions": contradictions,
        "reconciled": len(contradictions) == 0,
        "summary": (
            f"Memory reconciled via {authoritative.get('source', 'none')} authority."
            if layers
            else "Memory layers thin — no reconciliation required."
        ),
    }


def apply_precedence_confidence_adjustment(*, base_confidence: float, reconciliation: dict[str, Any]) -> float:
    confidence = base_confidence
    if reconciliation.get("reconciled"):
        confidence = min(0.95, confidence + 0.06)
    else:
        confidence = max(0.3, confidence - 0.12 * len(reconciliation.get("contradictions") or []))
    return confidence
