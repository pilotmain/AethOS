# SPDX-License-Identifier: Apache-2.0
"""Thread integrity runtime — operational thread integrity orchestration."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.continuity_reconstruction.continuity_decay import apply_decay_to_confidence, compute_continuity_decay
from aethos_core.continuity_reconstruction.thread_isolation import score_thread_isolation
from aethos_core.operational_context_memory.investigation_lifecycle import assess_investigation_lifecycle
from aethos_core.operational_context_memory.memory_precedence import (
    apply_precedence_confidence_adjustment,
    reconcile_memory_layers,
)


def assess_operational_thread_integrity(
    *,
    session_id: str = "default",
    channel: str = "chat",
    bridge: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reconciliation = reconcile_memory_layers(session_id=session_id, channel=channel)
    lifecycle = assess_investigation_lifecycle(session_id=session_id)

    investigations = reconciliation.get("investigations") or (bridge or {}).get("active_investigations") or []
    focus_topics = (bridge or {}).get("focus_topics") or []
    primary = reconciliation.get("primary_subject") or (bridge or {}).get("primary_subject")

    isolation = score_thread_isolation(
        investigations=investigations,
        focus_topics=focus_topics,
        primary_subject=primary,
    )

    stored_at = None
    for layer in reconciliation.get("layers") or []:
        if layer.get("updated_at"):
            stored_at = layer["updated_at"]
            break
        if layer.get("snapshot_at"):
            stored_at = layer["snapshot_at"]
            break

    age_hours = (time() - float(stored_at)) / 3600.0 if stored_at else 0.0
    decay = compute_continuity_decay(age_hours=age_hours)

    base_confidence = float((bridge or {}).get("continuity_confidence") or 0.5)
    confidence = apply_decay_to_confidence(base_confidence=base_confidence, age_hours=age_hours)
    confidence = apply_precedence_confidence_adjustment(base_confidence=confidence, reconciliation=reconciliation)
    if isolation.get("conflated"):
        confidence = max(0.3, confidence - 0.1)

    integrity_qualified = (
        reconciliation.get("reconciled", True)
        and not isolation.get("conflated")
        and decay.get("relevance_weight", 0) >= 0.4
    )

    return {
        "memory_reconciliation": reconciliation,
        "investigation_lifecycle": lifecycle,
        "thread_isolation": isolation,
        "continuity_decay": decay,
        "continuity_confidence": round(confidence, 2),
        "integrity_qualified": integrity_qualified,
        "summary": "Operational thread integrity active — decay, isolation, and memory precedence applied.",
    }
