# SPDX-License-Identifier: Apache-2.0
"""FIX 125C — patch proposal lifecycle receipts."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_SCHEMA_VERSION

_RECEIPTS: dict[str, list[dict[str, Any]]] = {}


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "software_delivery_patch_receipts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(plan_id: str) -> Path:
    safe = (plan_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_patch_receipts.json"


def clear_for_tests() -> None:
    from aethos_core.software_delivery.test_data_guard import tests_may_clear_persisted_data

    if not tests_may_clear_persisted_data():
        return
    _RECEIPTS.clear()
    if _store_dir().exists():
        for child in _store_dir().glob("*_patch_receipts.json"):
            child.unlink(missing_ok=True)


def list_patch_receipts(*, plan_id: str) -> list[dict[str, Any]]:
    if plan_id in _RECEIPTS:
        return list(_RECEIPTS[plan_id])
    path = _path(plan_id)
    if not path.is_file():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(rows, list):
        _RECEIPTS[plan_id] = list(rows)
        return list(rows)
    return []


def record_patch_receipt(
    *,
    plan_id: str,
    phase: str,
    status: str = "patch_proposal_rehearsal_success",
    detail: str = "",
    proposal_id: str = "",
    files: list[str] | None = None,
    blockers: list[str] | None = None,
) -> dict[str, Any]:
    receipt = {
        "receipt_id": f"spr-{uuid.uuid4().hex[:12]}",
        "plan_id": plan_id,
        "proposal_id": proposal_id,
        "phase": phase,
        "status": status,
        "detail": detail,
        "files": list(files or []),
        "blockers": list(blockers or []),
        "file_write_performed": False,
        "mutation_performed": False,
        "execution_mode": "software_delivery_patch_proposal_simulation",
        "schema_version": PATCH_PROPOSAL_SCHEMA_VERSION,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    rows = list_patch_receipts(plan_id=plan_id)
    rows.append(receipt)
    _RECEIPTS[plan_id] = rows
    _path(plan_id).write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return receipt
