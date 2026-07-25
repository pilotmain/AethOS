# SPDX-License-Identifier: Apache-2.0
"""Proactive automation scheduler — tick due scheduled tasks."""

from __future__ import annotations

import asyncio
import threading
from datetime import datetime, timezone
from time import time
from typing import Any

from aethos_core.automation.cron_match import cron_matches
from aethos_core.automation.executor import automation_enabled, execute_scheduled_task
from aethos_core.automation.store import list_all_enabled_scheduled_tasks

_lock = threading.Lock()
_running = False
_task: asyncio.Task | None = None
_last_cron_slot: dict[str, str] = {}
_stats: dict[str, Any] = {"ticks": 0, "runs": 0, "errors": 0, "last_tick_at": None}


def scheduler_status() -> dict[str, Any]:
    return {
        "running": _running,
        "enabled": automation_enabled(),
        "stats": dict(_stats),
        "tracked_tasks": len(list_all_enabled_scheduled_tasks()),
    }


def start_automation_scheduler() -> None:
    global _running, _task
    if not automation_enabled():
        return
    with _lock:
        if _running:
            return
        _running = True
    try:
        loop = asyncio.get_running_loop()
        _task = loop.create_task(_scheduler_loop())
    except RuntimeError:
        thread = threading.Thread(target=_thread_runner, name="automation-scheduler", daemon=True)
        thread.start()


def stop_automation_scheduler() -> None:
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
        try:
            run_due_scheduled_tasks()
        except Exception:
            _stats["errors"] = int(_stats.get("errors") or 0) + 1
        await asyncio.sleep(30.0)


def _task_is_due(task: dict[str, Any], now: float) -> bool:
    kind = str(task.get("schedule_kind") or "interval")
    last = float(task.get("last_run_at") or 0)
    if kind == "interval":
        interval = max(60, int(task.get("interval_sec") or 3600))
        return now - last >= interval
    expr = str(task.get("cron_expression") or "").strip()
    if not expr:
        return False
    dt = datetime.fromtimestamp(now, tz=timezone.utc)
    slot = dt.strftime("%Y-%m-%d %H:%M")
    task_id = str(task.get("task_id") or "")
    if _last_cron_slot.get(task_id) == slot:
        return False
    if cron_matches(expr, dt):
        _last_cron_slot[task_id] = slot
        return True
    return False


def run_due_scheduled_tasks(*, force: bool = False) -> dict[str, Any]:
    """Manual tick for tests and ops — run tasks that are due."""
    if not automation_enabled() and not force:
        return {"ok": False, "reason": "proactive_automation_disabled", "ran": []}

    now = time()
    _stats["ticks"] = int(_stats.get("ticks") or 0) + 1
    _stats["last_tick_at"] = now
    ran: list[str] = []
    for task in list_all_enabled_scheduled_tasks():
        task_id = str(task.get("task_id") or "")
        if not task_id:
            continue
        if not _task_is_due(task, now) and not force:
            continue
        tenant_id = str(task.get("_tenant_id") or "default")
        result = execute_scheduled_task(task_id, tenant_id=tenant_id, force=force)
        if result.get("ok"):
            ran.append(task_id)
            _stats["runs"] = int(_stats.get("runs") or 0) + 1
    return {"ok": True, "ran": ran}


def reset_scheduler_state_for_tests() -> None:
    global _running, _task, _last_cron_slot, _stats
    _running = False
    _task = None
    _last_cron_slot = {}
    _stats = {"ticks": 0, "runs": 0, "errors": 0, "last_tick_at": None}
