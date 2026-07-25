# SPDX-License-Identifier: Apache-2.0
"""Build Vercel inventory from official API responses."""

from __future__ import annotations

from typing import Any

from aethos_core.browser.platforms.vercel.vercel_entities import (
    HealthState,
    VercelInventoryArtifact,
    VercelProject,
)
from aethos_core.browser.platforms.vercel.vercel_health_classifier import classify_project_health
from aethos_core.browser.platforms.vercel.vercel_inventory_builder import (
    build_full_inventory_report,
    build_inventory_artifact,
    build_operational_summary,
)
from aethos_core.connections.adapters import auth_method_label
from aethos_core.providers.vercel.api_client import list_projects, parse_project_record


def _health_from_api_state(state: str) -> HealthState:
    low = (state or "").lower()
    if low in ("ready", "completed"):
        return HealthState.LIKELY_HEALTHY
    if low in ("error", "failed", "canceled"):
        return HealthState.FAILED
    if low in ("building", "queued", "initializing"):
        return HealthState.UNKNOWN
    return HealthState.UNKNOWN


def projects_from_api_payload(items: list[dict[str, Any]]) -> tuple[list[VercelProject], list[dict[str, Any]]]:
    projects: list[VercelProject] = []
    api_records: list[dict[str, Any]] = []
    for item in items:
        record = parse_project_record(item)
        name = record["name"]
        if not name:
            continue
        api_records.append(record)
        prod_state = str(record.get("latest_production_state") or "unknown")
        preview_state = str(record.get("latest_preview_state") or "unknown")
        health = _health_from_api_state(prod_state if prod_state != "unknown" else preview_state)
        production_url = record.get("production_url")
        domains = list(record.get("domains") or [])
        project = VercelProject(
            name=name,
            status="active",
            health=health,
            deployment_status=prod_state,
            deployment_state=prod_state,
            last_deploy_state=prod_state,
            latest_deployment_state=prod_state,
            latest_deployment_scope="production" if prod_state != "unknown" else "unknown",
            production_url=str(production_url) if production_url else None,
            production_url_source="vercel_api" if production_url else None,
            production_url_confidence="api" if production_url else "none",
            production_url_verified=bool(production_url),
            known_domains=domains,
            git_repo=str(record.get("repo_link") or "") or None,
            environment="production" if production_url else None,
            operator_status="healthy" if health == HealthState.LIKELY_HEALTHY else "unknown",
            production_health="healthy" if prod_state == "ready" else "unknown",
            evidence=[
                "source:vercel_api",
                f"api_project_id:{record.get('id')}",
                f"framework:{record.get('framework') or 'unknown'}",
            ],
        )
        project.health = classify_project_health(project)
        projects.append(project)
    return projects, api_records


def build_inventory_from_api(token: str) -> VercelInventoryArtifact:
    raw = list_projects(token)
    projects, api_records = projects_from_api_payload(raw)
    return build_inventory_artifact(
        projects,
        extraction_method="vercel_api",
        extraction_debug={"api_projects": api_records, "api_project_count": len(api_records)},
    )


def build_api_inventory_report(
    token: str,
    *,
    title: str,
    job_type: str,
    credential_id: str,
) -> tuple[VercelInventoryArtifact, str, str]:
    artifact = build_inventory_from_api(token)
    summary = build_operational_summary(artifact)
    full = build_full_inventory_report(
        title=title,
        job_type=job_type,
        profile_id=credential_id,
        site="vercel.com",
        page_title="Vercel API",
        url="https://api.vercel.com/v9/projects",
        artifact=artifact,
        login_wall=False,
        auth_method=auth_method_label("api_token"),
        tool_used="vercel_api",
        platform="vercel_api",
        browser_used=False,
        provider_used="none",
        masked_credential=f"{credential_id} (masked)",
    )
    return artifact, summary, full
