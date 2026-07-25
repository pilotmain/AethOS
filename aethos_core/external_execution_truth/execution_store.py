# SPDX-License-Identifier: Apache-2.0
"""External execution metadata store — Phase 11.8.1."""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any


def _store_path() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "external_execution"
    root.mkdir(parents=True, exist_ok=True)
    return root / "execution_meta.json"


def _load_all() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"jobs": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"jobs": {}}


def _save_all(data: dict[str, Any]) -> None:
    data["updated_at"] = time()
    _store_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_execution_meta(job_id: str) -> dict[str, Any] | None:
    jobs = _load_all().get("jobs") or {}
    row = jobs.get(job_id)
    return dict(row) if row else None


def upsert_execution_meta(job_id: str, **fields: Any) -> dict[str, Any]:
    data = _load_all()
    jobs: dict[str, Any] = dict(data.get("jobs") or {})
    row = dict(jobs.get(job_id) or {})
    row.update(fields)
    row["job_id"] = job_id
    row["updated_at"] = time()
    jobs[job_id] = row
    data["jobs"] = jobs
    _save_all(data)
    return row


def list_execution_meta(*, session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    jobs = list((_load_all().get("jobs") or {}).values())
    if session_id:
        jobs = [j for j in jobs if j.get("session_id") == session_id]
    jobs.sort(key=lambda j: float(j.get("updated_at") or 0), reverse=True)
    return jobs[:limit]


def clear_external_execution_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
