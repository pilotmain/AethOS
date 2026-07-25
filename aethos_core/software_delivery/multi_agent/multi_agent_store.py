# SPDX-License-Identifier: Apache-2.0
"""FIX 127 — multi-agent collaboration durable state."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.multi_agent.multi_agent_contract import (
    EXECUTOR_AGENT_ENABLED_FIX_127,
    MULTI_AGENT_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_127,
    SELF_AUTHORIZING_FIX_127,
)

_PLAN_INDEX: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_multi_agent_collaborations"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(collaboration_id: str) -> Path:
    safe = (collaboration_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _PLAN_INDEX.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_collaboration(*, collaboration_id: str) -> dict[str, Any] | None:
    path = _path(collaboration_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_collaboration_for_plan(*, plan_id: str) -> dict[str, Any] | None:
    cid = _PLAN_INDEX.get(plan_id)
    if cid:
        return load_collaboration(collaboration_id=cid)
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict) and str(payload.get("plan_id") or "") == plan_id:
            collaboration_id = str(payload.get("collaboration_id") or "")
            if collaboration_id:
                _PLAN_INDEX[plan_id] = collaboration_id
            return payload
    return None


def save_collaboration(record: dict[str, Any]) -> dict[str, Any]:
    collaboration_id = str(record.get("collaboration_id") or "").strip()
    if not collaboration_id:
        raise ValueError("collaboration_id required")
    record.setdefault("schema_version", MULTI_AGENT_SCHEMA_VERSION)
    record["executor_agent_enabled"] = EXECUTOR_AGENT_ENABLED_FIX_127
    record["mutation_performed"] = MUTATION_PERFORMED_FIX_127
    record["self_authorizing"] = SELF_AUTHORIZING_FIX_127
    record["updated_at"] = datetime.now(UTC).isoformat()
    _path(collaboration_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    plan_id = str(record.get("plan_id") or "")
    if plan_id:
        _PLAN_INDEX[plan_id] = collaboration_id
    return record
