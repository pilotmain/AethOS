# SPDX-License-Identifier: Apache-2.0
"""Distributed scheduler — HA operational cycle coordination."""

from __future__ import annotations

from time import time
from typing import Any

from aethos_core.runtime.distributed.worker_leases import acquire_lease, release_lease


def run_distributed_cycle(*, cycle_name: str, worker_id: str, runner) -> dict[str, Any]:
    """Run scheduler cycle with lease — only one worker executes at a time."""
    lease_key = f"scheduler:{cycle_name}"
    acquired = acquire_lease(resource_key=lease_key, worker_id=worker_id)
    if not acquired.get("ok"):
        return {
            "ok": False,
            "skipped": True,
            "reason": "lease_held",
            "held_by": acquired.get("held_by"),
        }
    try:
        result = runner()
        return {"ok": True, "cycle": cycle_name, "worker_id": worker_id, "result": result, "at": time()}
    finally:
        release_lease(resource_key=lease_key, worker_id=worker_id)


def distributed_scheduler_status() -> dict[str, Any]:
    from aethos_core.runtime.distributed.worker_leases import list_active_leases
    from aethos_core.runtime.schedulers.observation_scheduler import scheduler_status

    return {
        "scheduler": scheduler_status(),
        "active_leases": list_active_leases(),
        "ha_mode": True,
    }
