# SPDX-License-Identifier: Apache-2.0
"""External execution truth aggregate — Phase 11.8.1/11.8.2."""

from __future__ import annotations

from typing import Any

from aethos_core.external_execution_truth.execution_divergence import assess_execution_divergence
from aethos_core.external_execution_truth.execution_store import list_execution_meta
from aethos_core.external_execution_truth.external_runner_presence import assess_external_runner_presence
from aethos_core.external_execution_truth.orphaned_job_detection import detect_orphaned_jobs
from aethos_core.external_execution_truth.runtime_truth_bridge import enrich_job_with_execution_truth
from aethos_core.external_execution_truth.trigger_dispatch_truth import resolve_runner_mode, trigger_settings
from aethos_core.external_execution_truth.webhook_reconciliation import reconcile_stale_callbacks
from aethos_core.external_execution_truth.webhook_security import _secret
from aethos_core.jobs.job_state import list_jobs


def assess_external_execution_runtime(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    settings = trigger_settings()
    mode = resolve_runner_mode()
    presence = assess_external_runner_presence(session_id=session_id)
    reconciliation = reconcile_stale_callbacks(session_id=session_id)
    orphaned = detect_orphaned_jobs(session_id=session_id)
    jobs = [enrich_job_with_execution_truth(j) for j in list_jobs(session_id=session_id, limit=20)]
    divergences = [
        assess_execution_divergence(job_id=str(j.get("job_id") or ""))
        for j in jobs[:8]
        if j.get("execution_meta")
    ]
    divergent_count = sum(1 for d in divergences if d.get("divergent"))
    qualified = mode == "embedded" or (mode in {"external", "degraded"} and divergent_count == 0)
    webhook_hardened = bool(_secret())
    return {
        "ok": True,
        "phase": "11.8.2",
        "channel": channel,
        "session_id": session_id,
        "runner_mode": mode,
        "trigger_settings": {
            "enabled": settings["enabled"],
            "env": settings["env"],
            "max_retries": settings["max_retries"],
            "stale_callback_minutes": settings["stale_callback_minutes"],
            "orphaned_job_minutes": settings["orphaned_job_minutes"],
        },
        "external_runner_presence": presence,
        "reconciliation": reconciliation,
        "orphaned_jobs": orphaned,
        "jobs": jobs,
        "execution_meta_count": len(list_execution_meta(session_id=session_id)),
        "divergent_count": divergent_count,
        "webhook_security": {
            "signature_validation": webhook_hardened,
            "idempotency_keys": True,
            "callback_sequencing": True,
            "replay_protection": webhook_hardened,
            "orphan_reconciliation": True,
            "callback_truth_windows": True,
        },
        "converged": qualified,
        "summary": (
            "External execution truth active — webhook freshness, retry realism, and orphan reconciliation enabled."
            if settings["enabled"]
            else "Embedded execution truth — external runner ready when Trigger.dev is enabled."
        ),
        "principle": (
            "External execution failures, delays, retries, and stale callbacks must degrade trust gracefully."
        ),
    }
