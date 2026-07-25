# SPDX-License-Identifier: Apache-2.0
"""Immutable execution receipts under data/railway_execution_receipts/."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_RECEIPTS_BY_EXECUTION: dict[str, list[dict[str, Any]]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_execution_receipts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _receipts_path(execution_id: str) -> Path:
    safe = (execution_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_receipts.json"


def record_execution_receipt(
    *,
    execution_id: str,
    phase: str,
    status: str = "simulated",
    mutation_performed: bool = False,
    detail: str = "",
    started_at: str = "",
    completed_at: str = "",
    duration_ms: int | None = None,
    replayed: bool = False,
    skipped_existing: bool = False,
    receipt_group: str = "",
    env_var_names: list[str] | None = None,
    rollback_phase: str = "",
    rollback_action: str = "",
) -> dict[str, Any]:
    now = datetime.now(UTC).isoformat()
    receipt = {
        "receipt_id": f"rrec-{uuid.uuid4().hex[:12]}",
        "execution_id": execution_id,
        "phase": phase,
        "timestamp": started_at or now,
        "started_at": started_at or now,
        "completed_at": completed_at or now,
        "status": status,
        "mutation_performed": mutation_performed,
        "detail": detail,
        "replayed": replayed,
        "skipped_existing": skipped_existing,
    }
    if duration_ms is not None:
        receipt["duration_ms"] = duration_ms
    if receipt_group:
        receipt["receipt_group"] = receipt_group
    if env_var_names is not None:
        receipt["env_var_names"] = [str(n).upper() for n in env_var_names if str(n).strip()]
    if rollback_phase:
        receipt["rollback_phase"] = rollback_phase
    if rollback_action:
        receipt["rollback_action"] = rollback_action
    rows = list(_RECEIPTS_BY_EXECUTION.get(execution_id) or [])
    rows.append(receipt)
    _RECEIPTS_BY_EXECUTION[execution_id] = rows
    _persist_receipt_rows(execution_id, rows)
    return receipt


def _persist_receipt_rows(execution_id: str, rows: list[dict[str, Any]]) -> None:
    try:
        _receipts_path(execution_id).write_text(json.dumps(rows, indent=2), encoding="utf-8")
    except OSError:
        pass


def is_rollback_receipt_phase(phase: str) -> bool:
    return str(phase or "").startswith("rollback_")


def list_rollback_receipts(*, execution_id: str) -> list[dict[str, Any]]:
    return [
        receipt
        for receipt in list_execution_receipts(execution_id=execution_id)
        if is_rollback_receipt_phase(str(receipt.get("phase") or ""))
    ]


def list_forward_phase_receipts(*, execution_id: str) -> list[dict[str, Any]]:
    from aethos_core.providers.railway.execution_contract.execution_contract_models import (
        EXECUTION_PHASES,
    )

    phase_set = set(EXECUTION_PHASES)
    return [
        receipt
        for receipt in list_execution_receipts(execution_id=execution_id)
        if str(receipt.get("phase") or "") in phase_set
    ]


def find_phase_receipt(*, execution_id: str, phase: str) -> dict[str, Any] | None:
    matched: dict[str, Any] | None = None
    for receipt in list_execution_receipts(execution_id=execution_id):
        if str(receipt.get("phase") or "") == phase:
            matched = receipt
    return matched


def find_phase_group_receipt(
    *,
    execution_id: str,
    phase: str,
    receipt_group: str,
) -> dict[str, Any] | None:
    matched: dict[str, Any] | None = None
    for receipt in list_execution_receipts(execution_id=execution_id):
        if str(receipt.get("phase") or "") != phase:
            continue
        if str(receipt.get("receipt_group") or "") == receipt_group:
            matched = receipt
    return matched


def record_rollback_simulation_receipts(
    *,
    execution_id: str,
    completed_phases: list[str],
) -> list[dict[str, Any]]:
    """Record simulated rollback receipts for phases completed before a dry-run failure."""
    receipts: list[dict[str, Any]] = []
    for phase in reversed(completed_phases):
        rollback_phase = f"rollback_{phase}"
        if find_phase_receipt(execution_id=execution_id, phase=rollback_phase):
            continue
        receipts.append(
            record_execution_receipt(
                execution_id=execution_id,
                phase=rollback_phase,
                status="simulated_success",
                mutation_performed=False,
                detail="dry_run rollback simulation",
            )
        )
    return receipts


def list_execution_receipts(*, execution_id: str) -> list[dict[str, Any]]:
    execution_id = (execution_id or "").strip()
    if not execution_id:
        return []
    cached = _RECEIPTS_BY_EXECUTION.get(execution_id)
    if cached is not None:
        return [_normalize_receipt_row(dict(row)) for row in cached]
    path = _receipts_path(execution_id)
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(raw, list):
        rows = [_normalize_receipt_row(dict(row)) for row in raw if isinstance(row, dict)]
        _RECEIPTS_BY_EXECUTION[execution_id] = rows
        return rows
    return []


def _normalize_receipt_row(receipt: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
        normalize_receipt_status,
    )

    if not receipt.get("started_at") and receipt.get("timestamp"):
        receipt["started_at"] = receipt["timestamp"]
    if not receipt.get("completed_at"):
        receipt["completed_at"] = receipt.get("started_at") or receipt.get("timestamp") or ""
    receipt.setdefault("replayed", False)
    receipt.setdefault("skipped_existing", False)
    receipt.setdefault("mutation_performed", False)
    return normalize_receipt_status(receipt)


def record_simulated_phase_receipts(*, execution_id: str) -> list[dict[str, Any]]:
    from aethos_core.providers.railway.execution_contract.execution_contract_models import (
        EXECUTION_PHASES,
    )

    receipts: list[dict[str, Any]] = []
    for phase in EXECUTION_PHASES:
        receipts.append(
            record_execution_receipt(
                execution_id=execution_id,
                phase=phase,
                status="simulated",
                mutation_performed=False,
            )
        )
    return receipts


def clear_for_tests() -> None:
    _RECEIPTS_BY_EXECUTION.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
