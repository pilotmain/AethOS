# SPDX-License-Identifier: Apache-2.0
"""Cluster runtime status."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.runtime.distributed.distributed_scheduler import distributed_scheduler_status
from aethos_core.runtime.distributed.queue_backend import get_queue_backend


def get_cluster_status() -> dict[str, Any]:
    """Runtime cluster snapshot for Mission Control."""
    from aethos_core.config import get_settings

    s = get_settings()
    queue = get_queue_backend().snapshot()
    sched = distributed_scheduler_status()

    try:
        from aethos_core.runtime.job_executor import job_executor

        job_busy = getattr(job_executor, "_busy", False)
    except Exception:
        job_busy = False

    return {
        "ok": True,
        "worker_mode": getattr(s, "worker_mode", "embedded"),
        "deployment_mode": getattr(s, "deployment_mode", "local"),
        "queue": queue,
        "scheduler": sched,
        "job_executor_busy": job_busy,
        "scaling_domains": [
            "research_runtime",
            "browser_runtime",
            "engineering_validation",
            "replay_reconstruction",
            "provider_polling",
            "operational_intelligence",
            "presence_cycles",
        ],
        "checked_at": time(),
        "worker_isolation": getattr(s, "worker_mode", "embedded") == "standalone",
    }
