# SPDX-License-Identifier: Apache-2.0
"""Action runtime — governed real-world operational actions."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from pathlib import Path

NEVER_ALLOWED = frozenset({
    "purchase", "banking", "destructive_action", "privilege_escalation",
    "credential_export", "hidden_browser_action",
})

APPROVAL_REQUIRED = frozenset({
    "email_draft", "calendar_schedule", "slack_post", "pr_generation",
    "provider_restart", "deployment_workflow", "workspace_execution",
    "browser_automation",
})


def _queue_path() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "action_runtime"
    root.mkdir(parents=True, exist_ok=True)
    return root / "pending_actions.json"


def _load_queue() -> list[dict[str, Any]]:
    path = _queue_path()
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _save_queue(rows: list[dict[str, Any]]) -> None:
    _queue_path().write_text(json.dumps(rows[:100], indent=2), encoding="utf-8")


def propose_action(*, action_type: str, payload: dict[str, Any] | None = None, session_id: str = "default") -> dict[str, Any]:
    """Propose a governed action — never executes silently."""
    if action_type in NEVER_ALLOWED:
        return {
            "ok": False,
            "blocked": True,
            "reason": f"Action '{action_type}' is never allowed.",
            "autonomous_execution_blocked": True,
        }
    requires_approval = action_type in APPROVAL_REQUIRED or True
    action_id = f"act-{uuid4().hex[:12]}"
    record = {
        "action_id": action_id,
        "action_type": action_type,
        "payload": payload or {},
        "session_id": session_id,
        "status": "pending_approval",
        "requires_approval": requires_approval,
        "created_at": time(),
        "autonomous_execution_blocked": True,
    }
    rows = _load_queue()
    rows.insert(0, record)
    _save_queue(rows)
    return {"ok": True, "action": record, "message": "Action queued for operator approval."}


def approve_action(*, action_id: str, operator_id: str = "operator") -> dict[str, Any]:
    rows = _load_queue()
    for row in rows:
        if row.get("action_id") == action_id:
            if row.get("status") != "pending_approval":
                return {"ok": False, "reason": "Action not pending approval."}
            row["status"] = "approved"
            row["approved_by"] = operator_id
            row["approved_at"] = time()
            _save_queue(rows)
            return {"ok": True, "action": row, "message": "Approved — execution remains evidence-first and auditable."}
    return {"ok": False, "reason": "Action not found."}


def list_pending_actions(*, session_id: str | None = None) -> dict[str, Any]:
    rows = _load_queue()
    if session_id:
        rows = [r for r in rows if r.get("session_id") == session_id]
    pending = [r for r in rows if r.get("status") == "pending_approval"]
    return {"ok": True, "pending": pending, "count": len(pending), "autonomous_execution_blocked": True}


def clear_action_queue_for_tests() -> None:
    path = _queue_path()
    if path.is_file():
        path.unlink()
