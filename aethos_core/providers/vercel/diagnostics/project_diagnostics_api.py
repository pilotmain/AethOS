# SPDX-License-Identifier: Apache-2.0
"""Vercel project diagnostics — list and resolve projects."""

from __future__ import annotations

from typing import Any

from aethos_core.chat.provider_inventory_format import vercel_health_from_state
from aethos_core.providers.vercel.api_client import (
    find_project_by_name,
    list_deployments,
    list_projects,
    parse_deployment_record,
    parse_project_record,
)
from aethos_core.providers.vercel.operations.project_details_api import fetch_project_details

_MAX_DEPLOYMENT_HEALTH_ENRICH = 25


def _enrich_project_deployment_health(token: str, record: dict[str, Any]) -> dict[str, Any]:
    row = dict(record)
    prod_state = str(row.get("latest_production_state") or "unknown")
    if prod_state.lower() not in {"", "unknown"}:
        health, reason = vercel_health_from_state(prod_state)
        row["health"] = health
        if reason:
            row["health_reason"] = reason
        return row

    project_id = str(row.get("id") or "")
    if not project_id:
        health, reason = vercel_health_from_state(prod_state)
        row["health"] = health
        row["health_reason"] = reason or "missing_project_id"
        return row

    try:
        team_id = str(row.get("team_id") or "") or None
        raw_deps = list_deployments(token, project_id=project_id, team_id=team_id, limit=5)
        resolved_state = "unknown"
        for dep in raw_deps:
            if not isinstance(dep, dict):
                continue
            parsed = parse_deployment_record(dep)
            target = str(parsed.get("target") or "").lower()
            state = str(parsed.get("state") or "unknown")
            if target == "production":
                resolved_state = state
                break
            if resolved_state == "unknown":
                resolved_state = state
        if resolved_state == "unknown" and not raw_deps:
            row["health_reason"] = "no_deployments"
        elif resolved_state == "unknown":
            row["health_reason"] = "no_production_deployment_found"
        row["latest_production_state"] = resolved_state
        health, reason = vercel_health_from_state(resolved_state)
        row["health"] = health
        if reason and not row.get("health_reason"):
            row["health_reason"] = reason
    except Exception as exc:
        row["health"] = "unknown"
        row["health_reason"] = f"deployment_lookup_failed:{str(exc)[:120]}"
    return row


def enrich_projects_with_deployment_health(
    token: str,
    projects: list[dict[str, Any]],
    *,
    max_enrich: int = _MAX_DEPLOYMENT_HEALTH_ENRICH,
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    enrich_count = 0
    for record in projects:
        if not isinstance(record, dict):
            continue
        prod_state = str(record.get("latest_production_state") or "unknown")
        if prod_state.lower() not in {"", "unknown"}:
            enriched.append(_enrich_project_deployment_health(token, record))
            continue
        if enrich_count >= max_enrich:
            row = dict(record)
            row["health"] = "unknown"
            row["health_reason"] = "enrichment_limit"
            enriched.append(row)
            continue
        enrich_count += 1
        enriched.append(_enrich_project_deployment_health(token, record))
    return enriched


def fetch_projects_list(token: str, *, limit: int = 20) -> dict[str, Any]:
    try:
        raw = list_projects(token, limit=limit)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "projects": []}
    projects = [parse_project_record(item) for item in raw if isinstance(item, dict)]
    projects = enrich_projects_with_deployment_health(token, projects)
    return {"ok": True, "project_count": len(projects), "projects": projects}


def resolve_project_name(token: str, *, project_hint: str = "") -> dict[str, Any]:
    hint = (project_hint or "").strip()
    if hint:
        project = find_project_by_name(token, hint)
        if project:
            return {
                "ok": True,
                "project_name": str(project.get("name") or hint),
                "resolved": "hint",
            }
        return {"ok": False, "error": f"Project `{hint}` not found via Vercel API.", "project_name": ""}

    listing = fetch_projects_list(token, limit=5)
    if not listing.get("ok"):
        return {"ok": False, "error": str(listing.get("error") or "Project list unavailable."), "project_name": ""}
    projects = list(listing.get("projects") or [])
    if len(projects) == 1:
        return {
            "ok": True,
            "project_name": str(projects[0].get("name") or ""),
            "resolved": "single_project",
        }
    if not projects:
        return {"ok": False, "error": "No Vercel projects returned from API.", "project_name": ""}
    return {
        "ok": False,
        "error": "multiple_projects",
        "project_name": "",
        "projects": projects[:5],
    }


def fetch_project_diagnostics(token: str, *, project_name: str) -> dict[str, Any]:
    details = fetch_project_details(token, project_name=project_name)
    listing = fetch_projects_list(token, limit=100)
    summary = None
    if listing.get("ok"):
        for row in listing.get("projects") or []:
            if str(row.get("name") or "").lower() == project_name.lower():
                summary = row
                break
    return {
        "ok": details.get("ok", False),
        "project_name": project_name,
        "details": details.get("details") or {},
        "summary": summary or {},
        "error": details.get("error"),
    }