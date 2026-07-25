# SPDX-License-Identifier: Apache-2.0
"""Workspace audit — immutable execution trail."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.workspace_runtime.paths import workspace_runtime_root


def record_workspace_audit(event: dict[str, Any]) -> dict[str, Any]:
    root = workspace_runtime_root() / "audit"
    root.mkdir(parents=True, exist_ok=True)
    record = {**event, "recorded_at": time()}
    path = root / f"{record.get('audit_id', 'audit')}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    index = root / "index.json"
    ids: list[str] = []
    if index.is_file():
        try:
            ids = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            ids = []
    aid = str(record.get("audit_id") or path.stem)
    if aid not in ids:
        ids.insert(0, aid)
    index.write_text(json.dumps(ids[:500], indent=2), encoding="utf-8")
    return record


def list_workspace_audit(*, limit: int = 40) -> list[dict[str, Any]]:
    root = workspace_runtime_root() / "audit"
    index = root / "index.json"
    if not index.is_file():
        return []
    try:
        ids = json.loads(index.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows: list[dict[str, Any]] = []
    for aid in ids[:limit]:
        path = root / f"{aid}.json"
        if path.is_file():
            try:
                rows.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
    return rows


def clear_workspace_audit_for_tests() -> None:
    root = workspace_runtime_root() / "audit"
    if root.is_dir():
        for p in root.glob("*.json"):
            p.unlink()
