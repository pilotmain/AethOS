# SPDX-License-Identifier: Apache-2.0
"""Observation schedulers — bounded periodic readonly jobs."""

from __future__ import annotations

import asyncio
import threading
from time import time
from typing import Any

from aethos_core.runtime.schedulers.scheduler_config import DEFAULT_SCHEDULES, ObservationSchedule

_lock = threading.Lock()
_running = False
_task: asyncio.Task | None = None
_last_run: dict[str, float] = {}
_stats: dict[str, Any] = {"cycles": 0, "last_cycle_at": None, "errors": 0}


def scheduler_status() -> dict[str, Any]:
    return {
        "running": _running,
        "schedules": [
            {
                "name": s.name,
                "interval_sec": s.interval_sec,
                "enabled": s.enabled,
                "last_run_at": _last_run.get(s.name),
            }
            for s in DEFAULT_SCHEDULES
        ],
        "stats": dict(_stats),
    }


def start_observation_scheduler() -> None:
    global _running, _task
    with _lock:
        if _running:
            return
        _running = True
    try:
        loop = asyncio.get_running_loop()
        _task = loop.create_task(_scheduler_loop())
    except RuntimeError:
        thread = threading.Thread(target=_thread_runner, name="observation-scheduler", daemon=True)
        thread.start()


def stop_observation_scheduler() -> None:
    global _running, _task
    with _lock:
        _running = False
    if _task and not _task.done():
        _task.cancel()
        _task = None


def _thread_runner() -> None:
    asyncio.run(_scheduler_loop())


async def _scheduler_loop() -> None:
    while _running:
        now = time()
        for schedule in DEFAULT_SCHEDULES:
            if not schedule.enabled:
                continue
            last = _last_run.get(schedule.name, 0.0)
            if now - last >= schedule.interval_sec:
                _run_observation(schedule.name)
                _last_run[schedule.name] = time()
        await asyncio.sleep(30.0)


def _run_observation(name: str) -> None:
    try:
        if name == "reality_loop_cycle":
            from aethos_core.operations.reality_loop import run_reality_loop_cycle

            run_reality_loop_cycle(source="scheduler")
            _stats["cycles"] = int(_stats.get("cycles") or 0) + 1
            _stats["last_cycle_at"] = time()
        elif name == "presence_cycle":
            from aethos_core.presence.presence_runtime import run_presence_cycle

            run_presence_cycle(session_id="scheduler", channel="scheduler")
        elif name == "deployment_health":
            _observe_deployment_health()
        elif name == "workflow_failures":
            _observe_workflow_failures()
        elif name == "dependency_cve":
            _observe_dependency_risk()
        elif name == "browser_evidence":
            _observe_browser_signals()
        elif name == "repo_drift":
            _observe_repo_drift()
        elif name == "continuous_monitors":
            from aethos_core.monitors import run_due_monitors

            run_due_monitors()
        elif name == "daily_digest":
            from aethos_core.digest import run_due_digests

            run_due_digests()
        elif name == "proactive_scan":
            from aethos_core.proactive import run_proactive_scan

            run_proactive_scan()
        from aethos_core.jobs.cron_bridge import maybe_enqueue_governed_observation_job

        maybe_enqueue_governed_observation_job(category=name, payload={"source": "observation_scheduler"})
    except Exception:
        _stats["errors"] = int(_stats.get("errors") or 0) + 1


def run_due_observations(*, force: bool = False) -> dict[str, Any]:
    """Manual tick for tests — run observations that are due."""
    ran: list[str] = []
    now = time()
    for schedule in DEFAULT_SCHEDULES:
        if not schedule.enabled:
            continue
        last = _last_run.get(schedule.name, 0.0)
        if force or now - last >= schedule.interval_sec:
            _run_observation(schedule.name)
            _last_run[schedule.name] = time()
            ran.append(schedule.name)
    return {"ok": True, "ran": ran}


def _observe_deployment_health() -> None:
    from aethos_core.agents.memory.operational_patterns import record_operational_event

    try:
        from aethos_core.agents.providers.deployment_intelligence import build_deployment_intelligence

        intel = build_deployment_intelligence("deployment health observation")
        restarts = int(intel.get("restart_count") or 0)
        if restarts >= 2:
            record_operational_event(
                category="deployment_instability",
                detail=f"{restarts} restart/failure signals observed",
                provider=str(intel.get("provider") or "railway"),
            )
    except Exception:
        pass


def _observe_workflow_failures() -> None:
    from aethos_core.agents.memory.operational_patterns import record_operational_event
    from aethos_core.intelligence.operational_memory import record_operational_memory

    memory = __import__(
        "aethos_core.agents.memory.operational_patterns",
        fromlist=["get_operational_patterns_memory"],
    ).get_operational_patterns_memory()
    events = memory.get("events") or []
    wf = [e for e in events if "workflow" in str(e.get("category", "")).lower()]
    if len(wf) >= 2:
        record_operational_event(category="flaky_workflow", detail="workflow instability observed")
        record_operational_memory(kind="flaky_workflow", detail="scheduler workflow observation", category="flaky_workflow")


def _observe_dependency_risk() -> None:
    from aethos_core.agents.memory.operational_patterns import record_operational_event

    record_operational_event(category="dependency_churn", detail="scheduled dependency risk scan")


def _observe_browser_signals() -> None:
    from aethos_core.agents.memory.operational_patterns import record_operational_event

    try:
        from aethos_core.browser.runtime.browser_artifacts import list_artifacts

        artifacts = list_artifacts(limit=5)
        failed = [a for a in artifacts if str(a.get("status") or "").lower() in ("failed", "error")]
        for row in failed[:2]:
            record_operational_event(
                category="browser_evidence_failure",
                detail=str(row.get("error") or row.get("target") or "browser capture failed"),
            )
    except Exception:
        pass


def _observe_repo_drift() -> None:
    from aethos_core.intelligence.operational_memory import record_operational_memory

    record_operational_memory(kind="repo_drift_scan", detail="scheduled repo drift observation", category="operational_drift")


def reset_scheduler_state_for_tests() -> None:
    global _running, _task, _last_run, _stats
    _running = False
    _task = None
    _last_run = {}
    _stats = {"cycles": 0, "last_cycle_at": None, "errors": 0}
