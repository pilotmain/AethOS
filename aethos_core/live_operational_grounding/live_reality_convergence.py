# SPDX-License-Identifier: Apache-2.0
"""Live reality convergence — provider truth + cross-surface + freshness."""

from __future__ import annotations

from typing import Any

from aethos_core.cross_surface_reality_convergence.convergence_runtime import orchestrate_cross_surface_convergence
from aethos_core.live_operational_grounding.provider_signal_binding import bind_provider_signals
from aethos_core.live_operational_grounding.signal_freshness_tracking import track_signal_freshness


def assess_live_reality_convergence(
    *,
    session_id: str = "default",
    channel: str = "chat",
    primary_subject: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Validate Telegram ↔ MC ↔ runtime truth after real operations."""
    cross_surface = orchestrate_cross_surface_convergence(session_id=session_id, channel=channel)
    provider_binding = bind_provider_signals(primary_subject=primary_subject, category=category)
    freshness = track_signal_freshness(
        session_id=session_id,
        channel=channel,
        provider_checked_at=provider_binding.get("checked_at"),
    )

    live_converged = (
        provider_binding.get("bound")
        and provider_binding.get("subject_aligned", False)
        and freshness.get("signals_fresh", False)
        and not cross_surface.get("drift_detected")
    )

    return {
        "cross_surface": cross_surface,
        "provider_binding": provider_binding,
        "freshness": freshness,
        "live_converged": live_converged,
        "missing_runtime_evidence": not provider_binding.get("bound"),
        "aligned_surfaces": cross_surface.get("surfaces_aligned"),
        "contradictory_surfaces": cross_surface.get("drift_detected"),
        "summary": (
            "Live operational reality converged across provider truth, surfaces, and freshness."
            if live_converged
            else "Live operational reality not fully converged — treat continuity as stabilizing, not proven."
        ),
    }
