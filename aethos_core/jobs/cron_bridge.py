# SPDX-License-Identifier: Apache-2.0
"""Bridge observation scheduler cycles to governed durable jobs."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings


def maybe_enqueue_governed_observation_job(*, category: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    settings = get_settings()
    if not getattr(settings, "cron_governed_jobs_enabled", False):
        return {"ok": False, "skipped": True, "reason": "cron_governed_jobs_disabled"}
    from aethos_core.runtime.authority import authority

    job = authority.create_job(
        title=f"Observation cycle: {category}",
        job_type="governed_observation_cycle",
        params={"category": category, "payload": dict(payload or {})},
        source="scheduler",
        session_id="scheduler",
        auto_run=True,
    )
    return {"ok": True, "job_id": job.id, "category": category}


def cron_governed_status(*, session_id: str = "scheduler") -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    enabled = bool(getattr(settings, "cron_governed_jobs_enabled", False))
    recent: list[dict[str, Any]] = []
    try:
        from aethos_core.runtime.jobs import job_store

        for job in job_store.list_all():
            if str(getattr(job, "job_type", "") or "") != "governed_observation_cycle":
                continue
            recent.append(
                {
                    "id": job.id,
                    "title": job.title,
                    "status": job.status,
                    "created_at": job.created_at,
                }
            )
        recent.sort(key=lambda row: float(row.get("created_at") or 0), reverse=True)
    except Exception:
        recent = []
    return {
        "ok": True,
        "enabled": enabled,
        "session_id": session_id,
        "recent_observation_jobs": recent[:10],
    }
