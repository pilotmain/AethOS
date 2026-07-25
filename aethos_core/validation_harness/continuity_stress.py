# SPDX-License-Identifier: Apache-2.0
"""Continuity stress validation — Phase 11.8.0."""

from __future__ import annotations

from typing import Any


def assess_continuity_stress(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.job_truth.honest_replies import build_job_truth_state

    state = build_job_truth_state(session_id=session_id)
    freshness = state.get("freshness") or {}
    tier = str(freshness.get("freshness_tier") or "unknown")
    healthy = tier in {"fresh", "aging"} or not state.get("continuity", {}).get("continuity_available")
    return {
        "ok": True,
        "scenario": "continuity_stress",
        "freshness_tier": tier,
        "stale_context_handling": "healthy" if tier != "stale" else "decay-aware",
        "continuity_quality": "preserved" if healthy else "degraded",
        "qualified": tier != "stale" or bool(state.get("stalled_jobs")),
    }
