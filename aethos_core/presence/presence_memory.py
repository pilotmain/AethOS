# SPDX-License-Identifier: Apache-2.0
"""Presence memory — operational continuity."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.presence.paths import presence_memory_root


def _path():
    return presence_memory_root() / "presence_memory.json"


def _load() -> dict[str, Any]:
    path = _path()
    if not path.is_file():
        return {
            "incidents": [],
            "deployments": [],
            "recommendations": [],
            "dismissed": [],
            "snoozed": [],
            "validations": [],
            "replay_refs": [],
        }
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"incidents": [], "deployments": [], "recommendations": [], "dismissed": [], "snoozed": [], "validations": [], "replay_refs": []}


def _save(data: dict[str, Any]) -> None:
    _path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_presence_event(*, kind: str, detail: str, payload: dict[str, Any] | None = None) -> None:
    data = _load()
    bucket = _bucket_for_kind(kind)
    rows = list(data.get(bucket) or [])
    rows.insert(0, {"at": time(), "kind": kind, "detail": detail[:300], "payload": payload or {}})
    data[bucket] = rows[:200]
    data["updated_at"] = time()
    _save(data)


def _bucket_for_kind(kind: str) -> str:
    if kind in ("deployment", "railway", "vercel"):
        return "deployments"
    if kind in ("validation_failed", "validation"):
        return "validations"
    if kind in ("recommendation", "recommendation_dismissed", "recommendation_snoozed"):
        return "recommendations"
    if kind == "replay":
        return "replay_refs"
    return "incidents"


def record_dismissed(recommendation_id: str) -> None:
    data = _load()
    dismissed = list(data.get("dismissed") or [])
    dismissed.insert(0, {"id": recommendation_id, "at": time()})
    data["dismissed"] = dismissed[:100]
    _save(data)


def record_snoozed(recommendation_id: str, *, until: float) -> None:
    data = _load()
    snoozed = list(data.get("snoozed") or [])
    snoozed.insert(0, {"id": recommendation_id, "until": until, "at": time()})
    data["snoozed"] = snoozed[:100]
    _save(data)


def presence_memory_snapshot(*, window_hours: int = 48) -> dict[str, Any]:
    data = _load()
    cutoff = time() - window_hours * 3600
    out: dict[str, Any] = {"window_hours": window_hours}
    for key in ("incidents", "deployments", "recommendations", "validations", "replay_refs"):
        rows = [r for r in (data.get(key) or []) if float(r.get("at") or 0) >= cutoff]
        out[key] = rows[:30]
        out[f"{key}_count"] = len(rows)
    out["dismissed"] = list(data.get("dismissed") or [])[:20]
    out["snoozed"] = list(data.get("snoozed") or [])[:20]
    return out


def clear_presence_memory_for_tests() -> None:
    path = _path()
    if path.is_file():
        path.unlink()
