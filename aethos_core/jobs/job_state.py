# SPDX-License-Identifier: Apache-2.0
"""Local durable job state — persisted job lifecycle."""

from __future__ import annotations

import json
import re
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4


def _root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "durable_jobs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _store_path() -> Path:
    return _root() / "durable_jobs.json"


def _load_all() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"jobs": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"jobs": []}


def _save_all(data: dict[str, Any]) -> None:
    data["updated_at"] = time()
    _store_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_job_record(
    *,
    job_type: str,
    session_id: str = "default",
    entity_name: str | None = None,
    params: dict[str, Any] | None = None,
    external_id: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    # Stamp the owning tenant at creation. Durable jobs run detached (an embedded
    # background thread with no request context), so the tenant must travel on the
    # record itself, never via the request ContextVar (Correction 1). Defaults to
    # the current request's tenant, or "default" in single-tenant mode.
    if tenant_id is None:
        from aethos_core.tenancy import get_current_tenant

        tenant_id = get_current_tenant()
    job_id = f"dj-{uuid4().hex[:12]}"
    row = {
        "job_id": job_id,
        "job_type": job_type,
        "session_id": session_id,
        "tenant_id": tenant_id,
        "entity_name": entity_name,
        "params": params or {},
        "status": "queued",
        "external_id": external_id,
        "retries": 0,
        "artifact_ref": None,
        "error": None,
        "created_at": time(),
        "started_at": None,
        "completed_at": None,
    }
    data = _load_all()
    jobs: list[dict[str, Any]] = list(data.get("jobs") or [])
    jobs.insert(0, row)
    data["jobs"] = jobs[:200]
    _save_all(data)
    return row


def update_job(job_id: str, **fields: Any) -> dict[str, Any] | None:
    data = _load_all()
    jobs: list[dict[str, Any]] = list(data.get("jobs") or [])
    for i, job in enumerate(jobs):
        if job.get("job_id") == job_id:
            merged = {**job, **fields}
            if "updated_at" not in fields:
                merged["updated_at"] = time()
            jobs[i] = merged
            data["jobs"] = jobs
            _save_all(data)
            return jobs[i]
    return None


def get_job(job_id: str) -> dict[str, Any] | None:
    for job in list_jobs(limit=200):
        if job.get("job_id") == job_id:
            return job
    return None


def list_jobs(*, session_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    jobs = list(_load_all().get("jobs") or [])
    if session_id:
        jobs = [j for j in jobs if j.get("session_id") == session_id]
    return jobs[:limit]


def list_active_jobs(*, session_id: str | None = None) -> list[dict[str, Any]]:
    active = {"queued", "running", "scheduled", "dispatching", "awaiting_callback", "retrying", "orphaned"}
    return [j for j in list_jobs(session_id=session_id, limit=100) if j.get("status") in active]


def clear_durable_jobs_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
