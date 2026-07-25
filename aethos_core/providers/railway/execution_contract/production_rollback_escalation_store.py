# SPDX-License-Identifier: Apache-2.0
"""FIX 120 — durable production rollback escalation tickets and audit trail."""

from __future__ import annotations

import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.production_rollback_escalation_contract import (
    AUTONOMOUS_PRODUCTION_ROLLBACK_PERMITTED,
    ESCALATION_SCHEMA_VERSION,
    RollbackDecisionState,
)

_STORE_ROOT = Path("data/railway_production_rollback_escalations")


def _path(execution_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in execution_id.strip())
    return _STORE_ROOT / f"{safe or 'unknown'}.json"


def clear_for_tests() -> None:
    if _STORE_ROOT.exists():
        for child in _STORE_ROOT.glob("*.json"):
            child.unlink(missing_ok=True)


def load_escalation(*, execution_id: str) -> dict[str, Any] | None:
    path = _path(execution_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def save_escalation(record: dict[str, Any]) -> dict[str, Any]:
    execution_id = str(record.get("execution_id") or "").strip()
    if not execution_id:
        raise ValueError("execution_id required")
    record.setdefault("escalation_id", f"prbesc-{uuid.uuid4().hex[:12]}")
    record.setdefault("schema_version", ESCALATION_SCHEMA_VERSION)
    record["autonomous_rollback_permitted"] = AUTONOMOUS_PRODUCTION_ROLLBACK_PERMITTED
    record["updated_at"] = datetime.now(UTC).isoformat()
    _STORE_ROOT.mkdir(parents=True, exist_ok=True)
    _path(execution_id).write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def append_audit_event(
    record: dict[str, Any],
    *,
    action: str,
    actor: str = "operator",
    state: str = "",
    detail: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    trail = list(record.get("audit_trail") or [])
    trail.append(
        {
            "event_id": f"aud-{uuid.uuid4().hex[:10]}",
            "action": action,
            "actor": actor,
            "state": state or str(record.get("decision_state") or ""),
            "detail": detail,
            "session_id": session_id,
            "recorded_at": datetime.now(UTC).isoformat(),
        }
    )
    record["audit_trail"] = trail
    return save_escalation(record)


def record_rollback_rehearsal_confirmation(
    record: dict[str, Any],
    *,
    phrase_kind: str,
    session_id: str = "",
) -> dict[str, Any]:
    confirmations = list(record.get("rollback_rehearsal_confirmations") or [])
    if any(str(c.get("kind") or "") == phrase_kind for c in confirmations):
        return record
    confirmations.append(
        {
            "kind": phrase_kind,
            "recorded_at": time.time(),
            "session_id": session_id,
        }
    )
    record["rollback_rehearsal_confirmations"] = confirmations
    return save_escalation(record)


def rollback_rehearsal_quorum_count(record: dict[str, Any]) -> int:
    kinds = {
        str(c.get("kind") or "")
        for c in (record.get("rollback_rehearsal_confirmations") or [])
    }
    return len(kinds)
