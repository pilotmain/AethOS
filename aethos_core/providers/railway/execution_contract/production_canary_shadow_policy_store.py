# SPDX-License-Identifier: Apache-2.0
"""FIX 122 — durable canary/shadow deployment policy bindings and evidence."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_contract import (
    AUTOMATIC_PROMOTION_PERMITTED,
    AUTOMATIC_TRAFFIC_MUTATION_PERMITTED,
    AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED,
    CANARY_SHADOW_POLICY_SCHEMA_VERSION,
)


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_production_canary_shadow_policies"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(execution_id: str) -> Path:
    safe = (execution_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_policy_record(*, execution_id: str) -> dict[str, Any] | None:
    path = _path(execution_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def save_policy_record(record: dict[str, Any]) -> dict[str, Any]:
    execution_id = str(record.get("execution_id") or "").strip()
    if not execution_id:
        raise ValueError("execution_id required")
    record.setdefault("policy_id", f"pcsp-{uuid.uuid4().hex[:12]}")
    record.setdefault("schema_version", CANARY_SHADOW_POLICY_SCHEMA_VERSION)
    record["autonomous_deployment_permitted"] = AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED
    record["automatic_traffic_mutation_permitted"] = AUTOMATIC_TRAFFIC_MUTATION_PERMITTED
    record["automatic_promotion_permitted"] = AUTOMATIC_PROMOTION_PERMITTED
    record["updated_at"] = datetime.now(UTC).isoformat()
    _path(execution_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def append_policy_event(
    record: dict[str, Any],
    *,
    action: str,
    detail: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    events = list(record.get("policy_events") or [])
    events.append(
        {
            "event_id": f"pce-{uuid.uuid4().hex[:10]}",
            "action": action,
            "detail": detail,
            "session_id": session_id,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
    )
    record["policy_events"] = events
    return save_policy_record(record)
