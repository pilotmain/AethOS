# SPDX-License-Identifier: Apache-2.0
"""Operational replay — immutable cycle timelines."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.paths import agent_artifacts_root


def _root():
    return agent_artifacts_root() / "operational_replay"


def store_operational_replay(*, cycle: dict[str, Any]) -> dict[str, Any]:
    replay_id = f"oreplay-{uuid4().hex[:12]}"
    record = {
        "replay_id": replay_id,
        "created_at": time(),
        "cycle": cycle,
        "anomaly_count": len(cycle.get("anomalies") or []),
        "recommendation_count": len(cycle.get("recommendations") or []),
        "readonly": True,
    }
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{replay_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    _update_index(replay_id)
    return record


def get_operational_replay(replay_id: str) -> dict[str, Any] | None:
    path = _root() / f"{replay_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_operational_replays(*, limit: int = 20) -> list[dict[str, Any]]:
    index = _root() / "index.json"
    if not index.is_file():
        return []
    try:
        ids = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for rid in ids[:limit]:
        row = get_operational_replay(str(rid))
        if row:
            rows.append(row)
    return rows


def _update_index(replay_id: str) -> None:
    index = _root() / "index.json"
    ids: list[str] = []
    if index.is_file():
        try:
            ids = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            ids = []
    ids.insert(0, replay_id)
    index.write_text(json.dumps(ids[:200], indent=2), encoding="utf-8")


def clear_operational_replays_for_tests() -> None:
    root = _root()
    if root.is_dir():
        for p in root.glob("*.json"):
            p.unlink()
