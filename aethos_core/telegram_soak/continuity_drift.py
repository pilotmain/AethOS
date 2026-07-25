# SPDX-License-Identifier: Apache-2.0
"""Continuity drift analysis — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

from aethos_core.job_truth.freshness_truth import session_freshness
from aethos_core.jobs.job_state import list_jobs


def assess_continuity_drift(*, session_id: str = "default") -> dict[str, Any]:
    jobs = list_jobs(session_id=session_id, limit=30)
    freshness = session_freshness(jobs=jobs)
    tier = str(freshness.get("freshness_tier") or "unknown")
    drift = "stable"
    if tier == "stale":
        drift = "degraded"
    elif tier == "aging":
        drift = "aging"
    return {
        "ok": True,
        "continuity_drift": drift,
        "freshness": freshness,
        "qualified": tier != "stale",
    }
