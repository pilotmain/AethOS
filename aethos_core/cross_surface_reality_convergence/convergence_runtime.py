# SPDX-License-Identifier: Apache-2.0
"""Convergence runtime — cross-surface reality convergence orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.cross_surface_reality_convergence.reality_drift_detection import detect_reality_drift
from aethos_core.cross_surface_reality_convergence.runtime_truth_binding import bind_runtime_truth
from aethos_core.cross_surface_reality_convergence.session_linking import link_session_surfaces
from aethos_core.cross_surface_reality_convergence.surface_alignment import extract_surface_subjects, score_surface_alignment
from aethos_core.operational_context_memory.cross_surface_bridge import merge_cross_surface_context
from aethos_core.operational_context_memory.memory_precedence import reconcile_memory_layers


def orchestrate_cross_surface_convergence(
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> dict[str, Any]:
    bridge = merge_cross_surface_context(session_id=session_id)
    linking = link_session_surfaces(session_id=session_id, channel=channel)
    surface_subjects = extract_surface_subjects(session_id=session_id, channel=channel)
    alignment = score_surface_alignment(surface_subjects=surface_subjects)
    reconciliation = reconcile_memory_layers(session_id=session_id, channel=channel)
    drift = detect_reality_drift(alignment=alignment, bridge=bridge, reconciliation=reconciliation)

    primary = reconciliation.get("primary_subject") or next(
        iter((surface_subjects.get("active_subjects") or {}).values()),
        None,
    )
    runtime_truth = bind_runtime_truth(primary_subject=primary)

    surfaces = list(dict.fromkeys((bridge.get("surfaces") or []) + linking.get("active_surfaces") or []))
    multi_surface = len(surfaces) >= 2 or alignment.get("active_surface_count", 0) >= 2

    convergence_qualified = (
        not drift.get("drift_detected")
        and alignment.get("surfaces_aligned", True)
        and (runtime_truth.get("subject_aligned", True) if runtime_truth.get("runtime_truth_bound") else True)
        and (multi_surface or alignment.get("active_surface_count", 0) >= 1)
    )

    return {
        "bridge": bridge,
        "session_linking": linking,
        "surface_subjects": surface_subjects,
        "alignment": alignment,
        "reconciliation": reconciliation,
        "drift": drift,
        "runtime_truth_binding": runtime_truth,
        "surfaces": surfaces,
        "surfaces_aligned": alignment.get("surfaces_aligned"),
        "drift_detected": drift.get("drift_detected"),
        "drift_score": drift.get("drift_score"),
        "runtime_truth_bound": runtime_truth.get("runtime_truth_bound"),
        "convergence_qualified": convergence_qualified,
        "summary": (
            "Cross-surface reality converged — Telegram, web chat, and Mission Control align."
            if convergence_qualified
            else "Cross-surface reality divergence detected — continuity confidence should be reduced."
        ),
    }
