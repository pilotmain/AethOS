# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — shadow rehearsal receipts (separate from staging execution receipts)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_RECEIPTS_BY_EXECUTION: dict[str, list[dict[str, Any]]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_production_shadow_receipts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _receipts_path(execution_id: str) -> Path:
    safe = (execution_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_shadow_receipts.json"


def clear_for_tests() -> None:
    _RECEIPTS_BY_EXECUTION.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*_shadow_receipts.json"):
            child.unlink(missing_ok=True)


def list_shadow_receipts(*, execution_id: str) -> list[dict[str, Any]]:
    if execution_id in _RECEIPTS_BY_EXECUTION:
        return list(_RECEIPTS_BY_EXECUTION[execution_id])
    path = _receipts_path(execution_id)
    if not path.is_file():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(rows, list):
        _RECEIPTS_BY_EXECUTION[execution_id] = list(rows)
        return list(rows)
    return []


def find_shadow_phase_receipt(*, execution_id: str, phase: str) -> dict[str, Any] | None:
    for row in list_shadow_receipts(execution_id=execution_id):
        if str(row.get("phase") or "") == phase:
            return row
    return None


def record_shadow_receipt(
    *,
    execution_id: str,
    phase: str,
    status: str = "shadow_rehearsal_success",
    detail: str = "",
    replayed: bool = False,
    skipped_existing: bool = False,
    policy_checks_passed: bool = True,
    policy_blockers: list[str] | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    receipt = {
        "receipt_id": f"shrec-{uuid.uuid4().hex[:12]}",
        "execution_id": execution_id,
        "phase": phase,
        "timestamp": now,
        "started_at": now,
        "completed_at": now,
        "status": status,
        "mutation_performed": False,
        "execution_mode": "production_shadow",
        "detail": detail or f"production shadow rehearsal: {phase}",
        "replayed": replayed,
        "skipped_existing": skipped_existing,
        "policy_checks_passed": policy_checks_passed,
        "policy_blockers": list(policy_blockers or []),
    }
    rows = list_shadow_receipts(execution_id=execution_id)
    rows.append(receipt)
    _RECEIPTS_BY_EXECUTION[execution_id] = rows
    try:
        _receipts_path(execution_id).write_text(json.dumps(rows, indent=2), encoding="utf-8")
    except OSError:
        pass
    return receipt
