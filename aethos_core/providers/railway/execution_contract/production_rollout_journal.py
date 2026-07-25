# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — production rollout orchestration journal."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    ROLLOUT_SCHEMA_VERSION,
    ROLLOUT_STAGES,
)


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_production_rollout_journals"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _journal_path(execution_id: str) -> Path:
    safe = (execution_id or "").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def clear_for_tests() -> None:
    if _store_dir().exists():
        for child in _store_dir().glob("*.json"):
            child.unlink(missing_ok=True)


def load_rollout_journal(*, execution_id: str) -> dict[str, Any] | None:
    path = _journal_path(execution_id)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def save_rollout_journal(journal: dict[str, Any]) -> dict[str, Any]:
    execution_id = str(journal.get("execution_id") or "").strip()
    if not execution_id:
        raise ValueError("rollout journal requires execution_id")
    journal.setdefault("schema_version", ROLLOUT_SCHEMA_VERSION)
    journal["updated_at"] = datetime.now(UTC).isoformat()
    _journal_path(execution_id).write_text(json.dumps(journal, indent=2), encoding="utf-8")
    return journal


def get_or_create_rollout_journal(
    *,
    execution_id: str,
    session_id: str = "",
    plan: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    existing = load_rollout_journal(execution_id=execution_id)
    if existing:
        return existing, False
    plan = plan or {}
    journal = {
        "rollout_id": f"proll-{uuid.uuid4().hex[:12]}",
        "execution_id": execution_id,
        "session_id": session_id,
        "schema_version": ROLLOUT_SCHEMA_VERSION,
        "orchestration_state": "active",
        "current_stage": ROLLOUT_STAGES[0],
        "completed_stages": [],
        "stage_status": {stage: "pending" for stage in ROLLOUT_STAGES},
        "rollout_paused": False,
        "paused_at_stage": "",
        "blast_radius": "local",
        "health_checkpoints": {},
        "autonomous_promotion_permitted": False,
        "live_mutation_boundary": "blocked",
        "environment": str(plan.get("environment") or ""),
        "created_at": datetime.now(UTC).isoformat(),
    }
    return save_rollout_journal(journal), True
