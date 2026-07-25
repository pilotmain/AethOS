# SPDX-License-Identifier: Apache-2.0
"""FIX 134 — UI approval audit visibility and replay protection."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_execution_contract import (
    APPROVAL_EXECUTION_SCHEMA_VERSION,
    CHAT_GOVERNANCE_REQUIRED,
    UI_APPROVAL_CHANNEL,
    UI_APPROVAL_ORIGIN,
)


def audit_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "mission_control_ui_approval_audit"
    root.mkdir(parents=True, exist_ok=True)
    return root


def clear_ui_approval_audit_for_tests() -> None:
    if audit_dir().exists():
        for child in audit_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def list_ui_approval_audits(*, session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(audit_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        if session_id and str(payload.get("session_id") or "") != session_id:
            continue
        rows.append(payload)
        if len(rows) >= limit:
            break
    return rows


def find_replay_audit(*, session_id: str, inbox_id: str) -> dict[str, Any] | None:
    for row in list_ui_approval_audits(session_id=session_id, limit=200):
        if str(row.get("inbox_id") or "") != inbox_id:
            continue
        if row.get("gate_satisfied") is True or row.get("outcome") in {
            "success",
            "gate_already_cleared",
            "replay_protected",
        }:
            return row
    return None


def persist_ui_approval_audit(record: dict[str, Any]) -> dict[str, Any]:
    import uuid

    approval_id = str(record.get("approval_id") or f"mc-ui-apr-{uuid.uuid4().hex[:12]}")
    record.setdefault("approval_id", approval_id)
    record.setdefault("schema_version", APPROVAL_EXECUTION_SCHEMA_VERSION)
    record.setdefault("ui_origin", UI_APPROVAL_ORIGIN)
    record.setdefault("channel", UI_APPROVAL_CHANNEL)
    record.setdefault("chat_governance_required", CHAT_GOVERNANCE_REQUIRED)
    record.setdefault("direct_provider_mutation", False)
    record["recorded_at"] = datetime.now(UTC).isoformat()
    path = audit_dir() / f"{approval_id}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def audit_history_payload(*, session_id: str, limit: int = 40) -> dict[str, Any]:
    rows = list_ui_approval_audits(session_id=session_id, limit=limit)
    return {
        "ok": True,
        "session_id": session_id,
        "count": len(rows),
        "audits": rows,
    }
