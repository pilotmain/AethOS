# SPDX-License-Identifier: Apache-2.0
"""Job memory — durable job continuity per session."""

from __future__ import annotations

from typing import Any

from aethos_core.jobs.job_state import list_jobs


def build_job_continuity(*, session_id: str = "default") -> dict[str, Any]:
    jobs = list_jobs(session_id=session_id, limit=30)
    completed = [j for j in jobs if j.get("status") == "completed"]
    failed = [j for j in jobs if j.get("status") == "failed"]
    active = [j for j in jobs if j.get("status") in {
        "queued", "running", "scheduled", "dispatching", "awaiting_callback", "retrying", "orphaned",
    }]
    return {
        "session_id": session_id,
        "total_jobs": len(jobs),
        "active_jobs": active,
        "active_count": len(active),
        "completed_count": len(completed),
        "failed_count": len(failed),
        "latest_completed": completed[0] if completed else None,
        "continuity_available": bool(jobs),
    }
