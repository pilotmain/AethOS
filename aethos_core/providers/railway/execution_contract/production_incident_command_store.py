# SPDX-License-Identifier: Apache-2.0
"""FIX 123 — production incident command store."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.production_incident_command_contract import (
    AUTOMATIC_INCIDENT_CLOSURE_PERMITTED,
    AUTONOMOUS_INCIDENT_MUTATION_PERMITTED,
    AUTONOMOUS_INCIDENT_ROLLBACK_PERMITTED,
    INCIDENT_COMMAND_SCHEMA_VERSION,
)

_INDEX_BY_EXECUTION: dict[str, str] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_production_incidents"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(incident_id: str) -> Path:
    safe = (incident_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    _INDEX_BY_EXECUTION.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_incident(*, incident_id: str) -> dict[str, Any] | None:
    path = _path(incident_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_incident_for_execution(*, execution_id: str) -> dict[str, Any] | None:
    if execution_id in _INDEX_BY_EXECUTION:
        return load_incident(incident_id=_INDEX_BY_EXECUTION[execution_id])
    for path in _store_dir().glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if str(payload.get("execution_id") or "") == execution_id:
            if str(payload.get("status") or "") != "closed":
                _INDEX_BY_EXECUTION[execution_id] = str(payload.get("incident_id") or "")
                return payload
    return None


def save_incident(incident: dict[str, Any]) -> dict[str, Any]:
    incident_id = str(incident.get("incident_id") or "").strip()
    if not incident_id:
        raise ValueError("incident_id required")
    incident.setdefault("schema_version", INCIDENT_COMMAND_SCHEMA_VERSION)
    incident["mutation_performed"] = AUTONOMOUS_INCIDENT_MUTATION_PERMITTED
    incident["autonomous_rollback_permitted"] = AUTONOMOUS_INCIDENT_ROLLBACK_PERMITTED
    incident["automatic_closure_permitted"] = AUTOMATIC_INCIDENT_CLOSURE_PERMITTED
    incident["updated_at"] = datetime.now(UTC).isoformat()
    _path(incident_id).write_text(json.dumps(incident, indent=2), encoding="utf-8")
    execution_id = str(incident.get("execution_id") or "")
    if execution_id and str(incident.get("status") or "") != "closed":
        _INDEX_BY_EXECUTION[execution_id] = incident_id
    elif execution_id and execution_id in _INDEX_BY_EXECUTION:
        _INDEX_BY_EXECUTION.pop(execution_id, None)
    return incident


def append_incident_event(
    incident: dict[str, Any],
    *,
    action: str,
    actor: str = "operator",
    detail: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    events = list(incident.get("events") or [])
    events.append(
        {
            "timestamp": datetime.now(UTC).isoformat(),
            "actor": actor,
            "action": action,
            "detail": detail,
            "session_id": session_id,
            "mutation_performed": False,
        }
    )
    incident["events"] = events
    return save_incident(incident)


def append_incident_decision(
    incident: dict[str, Any],
    *,
    decision: str,
    actor: str = "operator",
    detail: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    decisions = list(incident.get("decisions") or [])
    decisions.append(
        {
            "decision_id": f"dec-{uuid.uuid4().hex[:10]}",
            "decision": decision,
            "actor": actor,
            "detail": detail,
            "session_id": session_id,
            "recorded_at": datetime.now(UTC).isoformat(),
            "mutation_performed": False,
        }
    )
    incident["decisions"] = decisions
    return save_incident(incident)
