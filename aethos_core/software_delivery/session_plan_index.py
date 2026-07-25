# SPDX-License-Identifier: Apache-2.0
"""Durable session → active plan binding (survives entity store test wipes)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _index_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_session_plan_index"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:64] or "default"
    return _index_dir() / f"{safe}.json"


def clear_session_plan_index_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    if _index_dir().exists():
        for child in _index_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_session_plan_id(*, session_id: str) -> str | None:
    sid = (session_id or "default").strip()[:64] or "default"
    path = _path(sid)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    plan_id = str(payload.get("plan_id") or "")
    return plan_id or None


def persist_session_plan_binding(*, session_id: str, plan_id: str) -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    pid = (plan_id or "").strip()
    if not pid:
        raise ValueError("plan_id required")
    record = {
        "schema_version": "software_delivery_session_plan_index_v1",
        "session_id": sid,
        "plan_id": pid,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    _path(sid).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record
