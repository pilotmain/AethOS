# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — production verification receipts (separate from staging/shadow phase receipts)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_production_verification_receipts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _path(execution_id: str) -> Path:
    safe = (execution_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_verification.json"


def clear_for_tests() -> None:
    if _store_dir().exists():
        for child in _store_dir().glob("*_verification.json"):
            child.unlink(missing_ok=True)


def load_verification_receipt(*, execution_id: str) -> dict[str, Any] | None:
    path = _path(execution_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def save_verification_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    execution_id = str(receipt.get("execution_id") or "").strip()
    if not execution_id:
        raise ValueError("execution_id required")
    receipt.setdefault("receipt_id", f"pvrec-{uuid.uuid4().hex[:12]}")
    receipt.setdefault("recorded_at", datetime.now(UTC).isoformat())
    receipt["mutation_performed"] = False
    receipt["schema_version"] = "production_verification_v1"
    _path(execution_id).write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return receipt
