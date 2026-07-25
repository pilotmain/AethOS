# SPDX-License-Identifier: Apache-2.0
"""Format provider inventory payloads as readable chat tables."""

from __future__ import annotations

from typing import Any


def vercel_health_from_state(state: str) -> tuple[str, str | None]:
    low = (state or "").strip().lower()
    if low in ("ready", "completed"):
        return "healthy", None
    if low in ("error", "failed", "canceled"):
        return "failed", None
    if low in ("building", "queued", "initializing"):
        return "deploying", None
    if not low or low == "unknown":
        return "unknown", "deployment_status_not_available"
    return "unknown", f"unrecognized_state:{low}"


def railway_health_from_deployment_state(dep_state: str, service_status: str = "") -> tuple[str, str, str | None]:
    from aethos_core.operational_planner.adapters.railway_wide_health import _classify_status_and_health

    status, health = _classify_status_and_health(service_status, dep_state)
    reason: str | None = None
    dep = (dep_state or "").strip().lower()
    if health == "unknown" and (not dep or dep == "unknown"):
        reason = "deployment_status_not_available"
    return status, health, reason


def normalize_vercel_inventory_rows(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    projects = list(inventory.get("projects") or [])
    if not projects and isinstance(inventory.get("inventory"), dict):
        projects = list((inventory.get("inventory") or {}).get("projects") or [])
    rows: list[dict[str, Any]] = []
    for row in projects:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("project") or "").strip()
        if not name:
            continue
        prod_state = str(
            row.get("latest_production_state")
            or row.get("latest_deployment_state")
            or row.get("deployment_state")
            or "unknown"
        )
        health = str(row.get("health") or row.get("production_health") or row.get("operator_status") or "")
        reason = row.get("health_reason")
        if not health or health == "unknown":
            health, derived_reason = vercel_health_from_state(prod_state)
            if derived_reason and not reason:
                reason = derived_reason
        rows.append(
            {
                "project": name,
                "service": name,
                "type": str(row.get("framework") or row.get("type") or "web"),
                "health": health,
                "health_reason": reason,
                "domain": str(row.get("production_url") or row.get("url") or "").strip(),
                "deployment_state": prod_state,
            }
        )
    return rows


def normalize_railway_inventory_rows(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    projects = list(inventory.get("projects") or [])
    for project in projects:
        if not isinstance(project, dict):
            continue
        project_name = str(project.get("name") or "")
        for environment in list(project.get("environments") or []):
            if not isinstance(environment, dict):
                continue
            env_name = str(environment.get("name") or "")
            for service in list(environment.get("services") or []):
                if not isinstance(service, dict):
                    continue
                service_name = str(service.get("name") or "")
                if not service_name:
                    continue
                dep_raw = service.get("latest_deployment")
                dep_state = "unknown"
                if isinstance(dep_raw, dict):
                    dep_state = str(dep_raw.get("status") or dep_raw.get("state") or "unknown")
                svc_status = str(service.get("status") or "unknown")
                health = str(service.get("health") or "")
                reason = service.get("health_reason")
                if not health:
                    svc_status, health, derived_reason = railway_health_from_deployment_state(dep_state, svc_status)
                    if derived_reason and not reason:
                        reason = derived_reason
                domain = str(service.get("domain") or "")
                if not domain and isinstance(dep_raw, dict):
                    domain = str(dep_raw.get("url") or "")
                rows.append(
                    {
                        "project": project_name,
                        "service": service_name,
                        "environment": env_name,
                        "type": str(service.get("type") or "web"),
                        "health": health,
                        "health_reason": reason,
                        "domain": domain,
                        "deployment_state": dep_state,
                        "service_id": str(service.get("id") or ""),
                    }
                )
    return rows


def format_inventory_table(
    rows: list[dict[str, Any]],
    *,
    max_rows: int | None = None,
) -> str:
    if not rows:
        return "No inventory rows returned."
    display = rows[:max_rows] if max_rows is not None else rows
    lines = [
        "| Project | Service | Type | Health | Domain |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in display:
        health_cell = str(row.get("health") or "unknown")
        reason = str(row.get("health_reason") or "").strip()
        if health_cell == "unknown" and reason:
            health_cell = f"unknown ({reason})"
        lines.append(
            f"| {row.get('project') or '—'} | {row.get('service') or '—'} | "
            f"{row.get('type') or '—'} | {health_cell} | {row.get('domain') or '—'} |"
        )
    if max_rows is not None and len(rows) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(rows)} rows._")
    return "\n".join(lines)


def normalize_github_inventory_rows(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    repos = list(inventory.get("repositories") or [])
    if not repos and isinstance(inventory.get("inventory"), dict):
        repos = list((inventory.get("inventory") or {}).get("repositories") or [])
    rows: list[dict[str, Any]] = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        full = str(repo.get("full_name") or repo.get("name") or "").strip()
        if not full:
            continue
        rows.append(
            {
                "repository": full,
                "owner": str(repo.get("owner") or (full.split("/")[0] if "/" in full else "")),
                "visibility": "private" if repo.get("private") else "public",
                "branch": str(repo.get("default_branch") or "main"),
                "updated": str(repo.get("updated_at") or "")[:10],
                "url": str(repo.get("html_url") or ""),
            }
        )
    return rows


def format_github_repos_table(inventory: dict[str, Any], *, max_rows: int | None = 30) -> str:
    rows = normalize_github_inventory_rows(inventory)
    if not rows:
        return "No repositories returned (check the GitHub token scope: `repo` + `read:org`)."
    display = rows[:max_rows] if max_rows is not None else rows
    lines = [
        "| Repository | Visibility | Branch | Updated |",
        "| --- | --- | --- | --- |",
    ]
    for row in display:
        lines.append(
            f"| {row.get('repository') or '—'} | {row.get('visibility') or '—'} | "
            f"{row.get('branch') or '—'} | {row.get('updated') or '—'} |"
        )
    if max_rows is not None and len(rows) > max_rows:
        lines.append(f"\n_…and {len(rows) - max_rows} more (showing {max_rows} most recent)._")
    return "\n".join(lines)


def format_vercel_projects_table(inventory: dict[str, Any], *, max_rows: int | None = None) -> str:
    return format_inventory_table(normalize_vercel_inventory_rows(inventory), max_rows=max_rows)


def format_railway_inventory_table(inventory: dict[str, Any], *, max_rows: int | None = None) -> str:
    return format_inventory_table(normalize_railway_inventory_rows(inventory), max_rows=max_rows)


def format_provider_inventory_table(
    provider: str,
    inventory: dict[str, Any],
    *,
    max_rows: int | None = None,
) -> str:
    canonical = (provider or "").strip().lower()
    if canonical == "vercel":
        return format_vercel_projects_table(inventory, max_rows=max_rows)
    if canonical == "railway":
        return format_railway_inventory_table(inventory, max_rows=max_rows)
    if canonical == "github":
        return format_github_repos_table(inventory, max_rows=max_rows if max_rows is not None else 30)
    rows = normalize_vercel_inventory_rows(inventory)
    if not rows:
        rows = normalize_railway_inventory_rows(inventory)
    return format_inventory_table(rows, max_rows=max_rows)


def build_inventory_result_payload(provider: str, inventory: dict[str, Any]) -> dict[str, Any]:
    canonical = (provider or "").strip().lower()
    if canonical == "vercel":
        rows = normalize_vercel_inventory_rows(inventory)
    elif canonical == "railway":
        rows = normalize_railway_inventory_rows(inventory)
    elif canonical == "github":
        rows = normalize_github_inventory_rows(inventory)
    else:
        rows = normalize_vercel_inventory_rows(inventory) or normalize_railway_inventory_rows(inventory)
    unknown_rows = [row for row in rows if str(row.get("health") or "") == "unknown"]
    return {
        "provider": canonical,
        "rows": rows,
        "inventory": inventory,
        "counts": {
            "total": len(rows),
            "healthy": sum(1 for row in rows if row.get("health") == "healthy"),
            "failed": sum(1 for row in rows if row.get("health") == "failed"),
            "deploying": sum(1 for row in rows if row.get("health") == "deploying"),
            "unknown": len(unknown_rows),
        },
        "unknown_rows": unknown_rows,
    }
