# SPDX-License-Identifier: Apache-2.0
"""Operational memory — recurring failures, mitigations, trends."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.agents.runtime.paths import agent_artifacts_root


def _path():
    return agent_artifacts_root() / "operational_memory.json"


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {"events": [], "mitigations": [], "trends": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"events": [], "mitigations": [], "trends": {}}


def _save(data: dict[str, Any]) -> None:
    path = _path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_operational_memory(
    *,
    kind: str,
    detail: str,
    category: str | None = None,
    provider: str | None = None,
    outcome: str | None = None,
) -> None:
    data = _load()
    events = list(data.get("events") or [])
    events.insert(
        0,
        {
            "at": time(),
            "kind": kind,
            "category": category,
            "provider": provider,
            "detail": detail[:300],
            "outcome": outcome,
        },
    )
    data["events"] = events[:500]
    if outcome == "mitigated":
        mitigations = list(data.get("mitigations") or [])
        mitigations.insert(0, {"at": time(), "kind": kind, "detail": detail[:200]})
        data["mitigations"] = mitigations[:100]
    _update_trends(data, kind=kind, category=category or kind)
    data["updated_at"] = time()
    _save(data)


def _update_trends(data: dict[str, Any], *, kind: str, category: str) -> None:
    trends = dict(data.get("trends") or {})
    key = category or kind
    entry = trends.get(key) or {"count": 0, "last_at": 0}
    entry["count"] = int(entry.get("count") or 0) + 1
    entry["last_at"] = time()
    trends[key] = entry
    data["trends"] = trends


def operational_memory_snapshot(*, window_hours: int = 168) -> dict[str, Any]:
    data = _load()
    cutoff = time() - window_hours * 3600
    events = [e for e in (data.get("events") or []) if float(e.get("at") or 0) >= cutoff]
    by_kind: dict[str, int] = {}
    for e in events:
        k = str(e.get("kind") or "unknown")
        by_kind[k] = by_kind.get(k, 0) + 1
    return {
        "total_events": len(events),
        "by_kind": by_kind,
        "mitigations": list(data.get("mitigations") or [])[:10],
        "trends": data.get("trends") or {},
        "recent_events": events[:30],
    }


def recurring_failure_kinds(*, min_count: int = 3, window_hours: int = 48) -> list[dict[str, Any]]:
    snap = operational_memory_snapshot(window_hours=window_hours)
    out: list[dict[str, Any]] = []
    for kind, count in (snap.get("by_kind") or {}).items():
        if count >= min_count:
            out.append({"kind": kind, "count": count})
    return sorted(out, key=lambda r: r["count"], reverse=True)


def clear_operational_memory_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
