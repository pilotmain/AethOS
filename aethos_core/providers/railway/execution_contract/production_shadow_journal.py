# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — production shadow journal (isolated from staging execution journal)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.production_shadow_contract_models import (
    PRODUCTION_SHADOW_EXECUTION_MODE,
)


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_production_shadow_journals"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _journal_path(execution_id: str) -> Path:
    safe = (execution_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_shadow_journal(*, execution_id: str) -> dict[str, Any] | None:
    path = _journal_path(execution_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def save_shadow_journal(journal: dict[str, Any]) -> dict[str, Any]:
    execution_id = str(journal.get("execution_id") or "").strip()
    if not execution_id:
        raise ValueError("shadow journal requires execution_id")
    journal["updated_at"] = datetime.now(UTC).isoformat()
    _journal_path(execution_id).write_text(json.dumps(journal, indent=2), encoding="utf-8")
    return journal


def get_or_create_shadow_journal(
    *,
    execution_id: str,
    plan: dict[str, Any],
    session_id: str = "",
) -> tuple[dict[str, Any], bool]:
    existing = load_shadow_journal(execution_id=execution_id)
    if existing:
        return existing, False
    journal = {
        "execution_id": execution_id,
        "session_id": session_id,
        "execution_mode": PRODUCTION_SHADOW_EXECUTION_MODE,
        "state": "shadow_rehearsal_initialized",
        "project": str(plan.get("project") or ""),
        "environment": str(plan.get("environment") or ""),
        "service_name": str(plan.get("service_name") or ""),
        "repo": str(plan.get("repo") or ""),
        "forward_shadow_completed": False,
        "rollback_shadow_completed": False,
        "phases": [],
        "created_at": datetime.now(UTC).isoformat(),
    }
    return save_shadow_journal(journal), True
