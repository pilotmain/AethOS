# SPDX-License-Identifier: Apache-2.0
"""Latest completed Vercel inventory job — fresher than stale operational memory."""

from __future__ import annotations

from typing import Any


def _project_from_dict(raw: dict[str, Any]) -> dict[str, Any]:
    name = str(raw.get("name") or "").strip().lower()
    if not name:
        return {}
    return {
        "name": name,
        "production_url": raw.get("production_url"),
        "production_url_source": raw.get("production_url_source"),
        "production_url_confidence": raw.get("production_url_confidence"),
        "production_url_verified": raw.get("production_url_verified"),
        "known_repo": raw.get("git_repo"),
        "git_repo": raw.get("git_repo"),
        "last_health": raw.get("health"),
        "health_confidence": raw.get("health_confidence") or raw.get("health"),
        "production_health": raw.get("production_health"),
        "latest_deployment_state": raw.get("latest_deployment_state"),
        "latest_deployment_scope": raw.get("latest_deployment_scope"),
        "operator_status": raw.get("operator_status"),
        "url_type": raw.get("url_type"),
        "attention_reason": raw.get("attention_reason"),
        "evidence": list(raw.get("evidence") or []),
        "environment": raw.get("environment"),
        "deployment_state": raw.get("deployment_state"),
    }


def get_latest_vercel_inventory_job() -> dict[str, Any] | None:
    from aethos_core.runtime.jobs import job_store

    candidates: list[tuple[float, Any]] = []
    for job in job_store.list_all():
        if job.job_type != "vercel_projects_inventory":
            continue
        if job.status.value != "completed":
            continue
        inv = job.params.get("vercel_inventory")
        if not isinstance(inv, dict):
            continue
        seen_at = float(job.updated_at or job.created_at or 0)
        candidates.append((seen_at, job))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    job = candidates[0][1]
    inv = job.params.get("vercel_inventory") or {}
    projects_raw = inv.get("projects") or []
    by_name: dict[str, dict[str, Any]] = {}
    for p in projects_raw:
        if not isinstance(p, dict):
            continue
        norm = _project_from_dict(p)
        if norm.get("name"):
            by_name[norm["name"]] = norm

    return {
        "job_id": job.id,
        "seen_at": job.updated_at or job.created_at,
        "projects_by_name": by_name,
        "inventory": inv,
    }


def _latest_inventory_job(*, job_type: str, inventory_key: str) -> dict[str, Any] | None:
    from aethos_core.runtime.jobs import job_store

    candidates: list[tuple[float, Any]] = []
    for job in job_store.list_all():
        if job.job_type != job_type:
            continue
        if job.status.value != "completed":
            continue
        inv = job.params.get(inventory_key)
        if not isinstance(inv, dict):
            continue
        seen_at = float(job.updated_at or job.created_at or 0)
        candidates.append((seen_at, job))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    job = candidates[0][1]
    inv = job.params.get(inventory_key) or {}
    return {"job_id": job.id, "seen_at": job.updated_at or job.created_at, "inventory": inv}


def get_latest_railway_inventory_job() -> dict[str, Any] | None:
    latest = _latest_inventory_job(job_type="railway_services_inventory", inventory_key="railway_inventory")
    if not latest:
        return None
    items = (latest.get("inventory") or {}).get("items") or []
    by_name: dict[str, dict[str, Any]] = {}
    for row in items:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("service_name") or "").strip().lower()
        if name:
            by_name[name] = row
    latest["services_by_name"] = by_name
    return latest


def get_latest_github_inventory_job() -> dict[str, Any] | None:
    latest = _latest_inventory_job(job_type="github_repositories_inventory", inventory_key="github_inventory")
    if not latest:
        return None
    items = (latest.get("inventory") or {}).get("items") or []
    by_name: dict[str, dict[str, Any]] = {}
    for row in items:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip().lower()
        if name:
            by_name[name] = row
    latest["repos_by_name"] = by_name
    return latest


def get_latest_project_state(project_name: str) -> dict[str, Any] | None:
    latest = get_latest_vercel_inventory_job()
    if not latest:
        return None
    key = (project_name or "").strip().lower()
    proj = latest["projects_by_name"].get(key)
    if not proj:
        return None
    return {
        **proj,
        "last_inventory_job_id": latest["job_id"],
        "inventory_seen_at": latest["seen_at"],
        "source": "latest_inventory_job",
    }


def merge_project_state(
    *,
    project_name: str | None,
    memory: dict[str, Any] | None,
) -> dict[str, Any]:
    """Prefer latest inventory job, fall back to operational memory."""
    if not project_name:
        return {"known_in_memory": False}

    latest = get_latest_project_state(project_name)
    mem = dict(memory or {})
    if latest:
        merged = {**mem, **latest, "known_in_memory": bool(mem)}
        merged["name"] = project_name
        return merged

    if not mem:
        return {"known_in_memory": False, "name": project_name}

    merged = {
        "known_in_memory": True,
        "name": project_name,
        "source": "operational_memory",
        "last_health": mem.get("last_health"),
        "health_confidence": mem.get("health_confidence"),
        "production_url": mem.get("production_url") or mem.get("known_production_url"),
        "production_url_source": mem.get("production_url_source"),
        "known_repo": mem.get("known_repo"),
        "last_seen_at": mem.get("last_seen_at"),
        "operator_status": mem.get("operator_status"),
        "production_health": mem.get("production_health"),
        "latest_deployment_state": mem.get("latest_deployment_state"),
        "latest_deployment_scope": mem.get("latest_deployment_scope"),
        "url_type": mem.get("url_type"),
        "evidence": list(mem.get("evidence") or []),
        "last_inventory_job_id": mem.get("last_inventory_job_id"),
        "inventory_seen_at": mem.get("last_seen_at"),
    }
    if not merged.get("latest_deployment_state") and merged.get("last_health") == "failed":
        merged["latest_deployment_state"] = "failed"
    return merged
