# SPDX-License-Identifier: Apache-2.0
"""Watch mode — readonly bounded operational watchers."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.presence.interruption_policy import mark_notified, should_notify
from aethos_core.presence.paths import presence_memory_root


def _path():
    return presence_memory_root() / "watchers.json"


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"watchers": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"watchers": {}}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def register_watcher(*, target: str, operator_id: str = "default") -> dict[str, Any]:
    allowed = {"railway_deployment", "github_workflow", "dependency_risk", "browser_anomalies", "workspace_drift"}
    if target not in allowed:
        return {"ok": False, "error": "target_not_allowed", "allowed": sorted(allowed)}
    watcher_id = f"watch-{uuid4().hex[:10]}"
    record = {
        "watcher_id": watcher_id,
        "target": target,
        "operator_id": operator_id,
        "readonly": True,
        "autonomous_actions": False,
        "created_at": time(),
        "last_tick_at": None,
        "cooldown_sec": 600,
        "status": "active",
    }
    data = _load()
    watchers = dict(data.get("watchers") or {})
    watchers[watcher_id] = record
    data["watchers"] = watchers
    _save(data)
    return {"ok": True, "watcher": record}


def list_watchers(*, limit: int = 20) -> list[dict[str, Any]]:
    rows = list((_load().get("watchers") or {}).values())
    rows.sort(key=lambda r: float(r.get("created_at") or 0), reverse=True)
    return rows[:limit]


def tick_watchers(*, focus: dict[str, Any] | None = None) -> dict[str, Any]:
    """Readonly watcher tick — may emit deduplicated alerts only."""
    data = _load()
    watchers = dict(data.get("watchers") or {})
    alerts: list[dict[str, str]] = []
    now = time()
    for wid, watcher in watchers.items():
        if watcher.get("status") != "active":
            continue
        last = float(watcher.get("last_tick_at") or 0)
        if now - last < float(watcher.get("cooldown_sec") or 600):
            continue
        alert = _check_watcher(watcher)
        watcher["last_tick_at"] = now
        if alert:
            fp = f"{watcher.get('target')}:{alert.get('summary', '')[:40]}"
            priority = alert.get("priority", "elevated")
            if should_notify(fingerprint=fp, priority=priority, focus_mode=(focus or {}).get("mode")):
                alerts.append(alert)
                mark_notified(fp)
        watchers[wid] = watcher
    data["watchers"] = watchers
    _save(data)
    return {"ok": True, "alerts": alerts, "autonomous_execution_blocked": True}


def _check_watcher(watcher: dict[str, Any]) -> dict[str, str] | None:
    target = str(watcher.get("target") or "")
    if target == "github_workflow":
        from aethos_core.agents.memory.operational_patterns import get_operational_patterns_memory

        mem = get_operational_patterns_memory()
        wf = sum(1 for e in (mem.get("events") or []) if "workflow" in str(e.get("category", "")).lower())
        if wf >= 2:
            return {"summary": "GitHub workflow instability detected", "priority": "urgent"}
    if target == "railway_deployment":
        from aethos_core.agents.memory.operational_patterns import get_operational_patterns_memory

        mem = get_operational_patterns_memory()
        dep = sum(1 for e in (mem.get("events") or []) if "deployment" in str(e.get("category", "")).lower())
        if dep >= 2:
            return {"summary": "Railway deployment instability observed", "priority": "urgent"}
    return None


def clear_watchers_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
