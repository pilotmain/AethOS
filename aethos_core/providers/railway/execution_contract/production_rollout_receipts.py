# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — rollout stage receipts (separate from shadow/verification receipts)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    ROLLOUT_RECEIPT_PHASE_PREFIX,
    ROLLOUT_SCHEMA_VERSION,
)

_RECEIPTS_BY_EXECUTION: dict[str, list[dict[str, Any]]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_production_rollout_receipts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _receipts_path(execution_id: str) -> Path:
    safe = (execution_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_rollout_receipts.json"


def clear_for_tests() -> None:
    _RECEIPTS_BY_EXECUTION.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*_rollout_receipts.json"):
            child.unlink(missing_ok=True)


def list_rollout_receipts(*, execution_id: str) -> list[dict[str, Any]]:
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


def record_rollout_receipt(
    *,
    execution_id: str,
    stage: str,
    action: str,
    status: str = "rollout_stage_recorded",
    detail: str = "",
    health_checkpoint: str = "",
    evidence_snapshot: dict[str, Any] | None = None,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"prr-{uuid.uuid4().hex[:12]}",
        "execution_id": execution_id,
        "phase": f"{ROLLOUT_RECEIPT_PHASE_PREFIX}{stage}",
        "stage": stage,
        "action": action,
        "status": status,
        "detail": detail,
        "health_checkpoint": health_checkpoint,
        "evidence_snapshot": evidence_snapshot or {},
        "blockers": list(blockers or []),
        "mutation_performed": False,
        "autonomous_promotion": False,
        "execution_mode": "production_rollout_simulation",
        "schema_version": ROLLOUT_SCHEMA_VERSION,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    rows = list_rollout_receipts(execution_id=execution_id)
    rows.append(receipt)
    _RECEIPTS_BY_EXECUTION[execution_id] = rows
    _receipts_path(execution_id).write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return receipt
