# SPDX-License-Identifier: Apache-2.0
"""FIX 117 — durable operator confirmations for production quorum (no secrets)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Literal

ConfirmationKind = Literal[
    "production_final_phrase",
    "production_quorum_confirmation",
]

_STORE_ROOT = Path("data/railway_production_confirmations")


def _path(execution_id: str) -> Path:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in execution_id.strip())
    return _STORE_ROOT / f"{safe or 'unknown'}.json"


def clear_for_tests() -> None:
    if _STORE_ROOT.exists():
        for child in _STORE_ROOT.glob("*.json"):
            child.unlink(missing_ok=True)


def list_confirmations(*, execution_id: str) -> list[dict[str, Any]]:
    path = _path(execution_id)
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = payload.get("confirmations")
    return list(rows) if isinstance(rows, list) else []


def record_confirmation(
    *,
    execution_id: str,
    kind: ConfirmationKind,
    session_id: str = "",
) -> dict[str, Any]:
    if not execution_id.strip():
        raise ValueError("execution_id required")
    path = _path(execution_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list_confirmations(execution_id=execution_id)
    if any(str(r.get("kind") or "") == kind for r in rows):
        return {"recorded": False, "idempotent_replay": True, "kind": kind}
    row = {
        "kind": kind,
        "recorded_at": time.time(),
        "session_id": session_id,
    }
    rows.append(row)
    path.write_text(
        json.dumps({"execution_id": execution_id, "confirmations": rows}, indent=2),
        encoding="utf-8",
    )
    return {"recorded": True, "idempotent_replay": False, "kind": kind}


def quorum_counts(*, execution_id: str) -> dict[str, int]:
    rows = list_confirmations(execution_id=execution_id)
    kinds = {str(r.get("kind") or "") for r in rows}
    return {
        "production_final_phrase": int("production_final_phrase" in kinds),
        "production_quorum_confirmation": int("production_quorum_confirmation" in kinds),
        "total_distinct": len(kinds),
    }
