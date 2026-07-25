# SPDX-License-Identifier: Apache-2.0
"""Runtime supervision orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_supervision.process_observer import observe_processes
from aethos_core.runtime_supervision.resource_exhaustion import analyze_resource_exhaustion
from aethos_core.runtime_supervision.restart_patterns import detect_restart_patterns
from aethos_core.runtime_supervision.service_recovery import verify_service_recovery
from aethos_core.runtime_supervision.stabilization_runtime import observe_stabilization
from aethos_core.runtime_supervision.supervision_memory import record_supervision_event, supervision_memory_state


def observe_supervision_state(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    runtime_snapshot = runtime_snapshot or {}
    processes = observe_processes(runtime_snapshot=runtime_snapshot)
    restart_patterns = detect_restart_patterns(runtime_snapshot=runtime_snapshot)
    exhaustion = analyze_resource_exhaustion(runtime_snapshot=runtime_snapshot)
    recovery = None
    containers = runtime_snapshot.get("containers") or []
    if containers and isinstance(containers[0], dict):
        c = containers[0]
        recovery = verify_service_recovery(
            service_name=str(c.get("name") or "service"),
            before={"status": "recovering"},
            after=c,
        )
    stabilization = observe_stabilization(
        recovery_verified=bool(recovery and recovery.get("verified")),
        restart_patterns=restart_patterns,
    )
    record_supervision_event(event={"phase": stabilization.get("stabilization_phase"), "restart_loops": restart_patterns.get("restart_loops_detected", 0)})
    return {
        "ok": True,
        "processes": processes,
        "restart_patterns": restart_patterns,
        "exhaustion": exhaustion,
        "recovery": recovery,
        "stabilization": stabilization,
        "memory": supervision_memory_state(),
        "summary": recovery.get("summary") if recovery else processes.get("summary", ""),
    }
