# SPDX-License-Identifier: Apache-2.0
"""Replay bridge — hydrate operational replays into presence timeline."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.presence.paths import presence_artifacts_root


def build_presence_timeline(*, window_hours: int = 48) -> dict[str, Any]:
    """Merge subsystem events into unified operational timeline."""
    entries: list[dict[str, Any]] = []

    entries.extend(_entries_from_feed())
    entries.extend(_entries_from_operational_replay())
    entries.extend(_entries_from_workspace_replay())
    entries.extend(_entries_from_engineering_audit())

    cutoff = time() - window_hours * 3600
    entries = [e for e in entries if float(e.get("at") or 0) >= cutoff]
    entries.sort(key=lambda e: float(e.get("at") or 0), reverse=True)

    timeline_id = f"ptl-{uuid4().hex[:12]}"
    record = {
        "artifact_type": "presence_operational_timeline",
        "timeline_id": timeline_id,
        "created_at": time(),
        "window_hours": window_hours,
        "entries": entries[:80],
        "entry_count": len(entries),
        "readonly": True,
        "autonomous_execution_blocked": True,
    }
    path = presence_artifacts_root() / f"{timeline_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    _update_timeline_index(timeline_id)
    return record


def get_presence_timeline(timeline_id: str) -> dict[str, Any] | None:
    path = presence_artifacts_root() / f"{timeline_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_presence_timelines(*, limit: int = 10) -> list[dict[str, Any]]:
    index = presence_artifacts_root() / "timeline_index.json"
    if not index.is_file():
        return []
    try:
        ids = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for tid in ids[:limit]:
        row = get_presence_timeline(str(tid))
        if row:
            rows.append(row)
    return rows


def _update_timeline_index(timeline_id: str) -> None:
    index = presence_artifacts_root() / "timeline_index.json"
    ids: list[str] = []
    if index.is_file():
        try:
            ids = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            ids = []
    ids.insert(0, timeline_id)
    index.write_text(json.dumps(ids[:100], indent=2), encoding="utf-8")


def _entries_from_feed() -> list[dict[str, Any]]:
    from aethos_core.presence.operational_feed import list_feed_events

    return [
        {"at": e.get("created_at") or e.get("at"), "kind": "feed", "summary": e.get("summary"), "source": e.get("source")}
        for e in list_feed_events(limit=20)
    ]


def _entries_from_operational_replay() -> list[dict[str, Any]]:
    try:
        from aethos_core.intelligence.operational_replay import list_operational_replays

        entries: list[dict[str, Any]] = []
        for r in list_operational_replays(limit=5):
            entries.append(
                {
                    "at": r.get("created_at"),
                    "kind": "operational_replay",
                    "summary": f"Reality loop replay ({r.get('anomaly_count', 0)} anomalies)",
                    "replay_id": r.get("replay_id"),
                }
            )
        return entries
    except Exception:
        return []


def _entries_from_workspace_replay() -> list[dict[str, Any]]:
    try:
        from aethos_core.workspace_runtime.workspace_artifacts import list_workspace_runtime_artifacts

        return [
            {"at": a.get("created_at"), "kind": "workspace", "summary": a.get("summary"), "artifact_id": a.get("artifact_id")}
            for a in list_workspace_runtime_artifacts(limit=10)
            if "replay" in str(a.get("artifact_type", ""))
        ]
    except Exception:
        return []


def _entries_from_engineering_audit() -> list[dict[str, Any]]:
    try:
        from aethos_core.engineering.governance.engineering_audit import list_execution_records

        return [
            {
                "at": e.get("audit", {}).get("at") or e.get("recorded_at"),
                "kind": "engineering_execution",
                "summary": e.get("status"),
                "execution_id": e.get("execution_id"),
            }
            for e in list_execution_records(limit=8)
        ]
    except Exception:
        return []
