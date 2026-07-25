# SPDX-License-Identifier: Apache-2.0
"""Job truth runtime aggregate — Phase 11.8.0."""

from __future__ import annotations

from typing import Any

from aethos_core.job_truth.freshness_truth import session_freshness
from aethos_core.job_truth.honest_replies import build_job_truth_state
from aethos_core.job_truth.notification_policy import compose_notification_digest
from aethos_core.jobs.job_notifications import list_pending_notifications
from aethos_core.jobs.job_state import list_jobs


def assess_job_truth_runtime(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    state = build_job_truth_state(session_id=session_id)
    pending = list_pending_notifications(session_id=session_id)
    digest = compose_notification_digest(pending) if pending else ""
    freshness = state.get("freshness") or {}
    presence = state.get("runtime_presence") or {}
    qualified = bool(state.get("continuity")) and str(freshness.get("freshness_tier") or "") != "unknown"
    return {
        **state,
        "channel": channel,
        "converged": qualified,
        "notification_digest": digest,
        "summary": (
            "Job status honesty active — lifecycle truth, freshness bounds, and calm notification digest enabled."
            if qualified
            else "Job status honesty ready — awaiting durable job activity."
        ),
        "principle": (
            "AethOS must never sound more active or certain than runtime truth supports."
        ),
    }


def get_job_truth_notifications(*, session_id: str = "default") -> dict[str, Any]:
    pending = list_pending_notifications(session_id=session_id)
    return {
        "ok": True,
        "pending_count": len(pending),
        "digest": compose_notification_digest(pending),
        "notifications": pending[:10],
    }


def get_job_truth_freshness(*, session_id: str = "default") -> dict[str, Any]:
    jobs = list_jobs(session_id=session_id, limit=30)
    freshness = session_freshness(jobs=jobs)
    return {"ok": True, "session_id": session_id, **freshness}
