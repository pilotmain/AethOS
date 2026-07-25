# SPDX-License-Identifier: Apache-2.0
"""Engineering execution audit trail."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any

from aethos_core.agents.runtime.paths import agent_artifacts_root


def _audit_root() -> Path:
    return agent_artifacts_root() / "engineering_audit"


def record_execution(execution: dict[str, Any]) -> dict[str, Any]:
    eid = str(execution.get("execution_id") or "")
    if not eid:
        return execution
    root = _audit_root()
    root.mkdir(parents=True, exist_ok=True)
    record = {**execution, "recorded_at": time()}
    (root / f"{eid}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    index_path = root / "index.json"
    index: list[str] = []
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            index = []
    if eid not in index:
        index.insert(0, eid)
    index_path.write_text(json.dumps(index[:200], indent=2), encoding="utf-8")
    return record


def get_execution_record(execution_id: str) -> dict[str, Any] | None:
    path = _audit_root() / f"{execution_id}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def list_execution_records(*, limit: int = 20) -> list[dict[str, Any]]:
    index_path = _audit_root() / "index.json"
    if not index_path.is_file():
        return []
    try:
        ids = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for eid in ids[:limit]:
        rec = get_execution_record(str(eid))
        if rec:
            rows.append(rec)
    return rows
