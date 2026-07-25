# SPDX-License-Identifier: Apache-2.0
"""Webhook/runtime contradiction capture — Phase 11.8.2."""

from __future__ import annotations

from typing import Any

from aethos_core.external_execution_truth.execution_divergence import assess_execution_divergence
from aethos_core.jobs.job_state import list_jobs


def capture_contradictions(*, session_id: str = "default") -> dict[str, Any]:
    rows = [
        assess_execution_divergence(job_id=str(j.get("job_id") or ""))
        for j in list_jobs(session_id=session_id, limit=30)
    ]
    divergent = [r for r in rows if r.get("divergent")]
    phrase = None
    if divergent:
        phrase = (
            "Operational truth diverged between embedded continuity and external callback signals. "
            "Confidence is bounded until reconciliation completes."
        )
    return {
        "ok": True,
        "divergent_count": len(divergent),
        "divergences": divergent[:10],
        "reconciliation_phrase": phrase,
        "qualified": len(divergent) == 0,
    }
