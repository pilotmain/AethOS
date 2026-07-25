# SPDX-License-Identifier: Apache-2.0
"""Collect multi-source Vercel live readonly evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.vercel.diagnostics.build_log_analyzer import analyze_build_logs
from aethos_core.providers.vercel.diagnostics.domain_health_checker import check_domain_health
from aethos_core.providers.vercel.diagnostics.env_metadata_reader import read_env_metadata
from aethos_core.providers.vercel.diagnostics.project_diagnostics_api import (
    fetch_project_diagnostics,
    fetch_projects_list,
    resolve_project_name,
)
from aethos_core.providers.vercel.diagnostics.runtime_log_analyzer import analyze_runtime_logs
from aethos_core.providers.vercel.operations.deployments_api import fetch_deployments
from aethos_core.providers.vercel.operations.logs_api import fetch_deployment_logs


def collect_vercel_live_evidence(
    token: str,
    *,
    project_name: str = "",
    session_id: str = "default",
    operation: str = "live_diagnosis",
) -> dict[str, Any]:
    if operation == "projects":
        projects = fetch_projects_list(token)
        return {
            "ok": projects.get("ok", False),
            "operation": operation,
            "projects": projects,
            "project_name": "",
        }

    resolution = resolve_project_name(token, project_hint=project_name)
    if not resolution.get("ok"):
        return {
            "ok": False,
            "operation": operation,
            "error": resolution.get("error"),
            "projects": resolution.get("projects") or [],
            "project_name": "",
        }

    resolved_name = str(resolution.get("project_name") or "")
    project = fetch_project_diagnostics(token, project_name=resolved_name)
    deployments = fetch_deployments(token, project_name=resolved_name, limit=10)
    latest = _select_latest_deployment(deployments)
    failed = _select_failed_deployment(deployments)

    log_target = failed or latest
    logs = fetch_deployment_logs(
        token,
        project_name=resolved_name,
        deployment_id=str(log_target.get("id") or "") if log_target else None,
    )
    build_analysis = analyze_build_logs(logs)
    runtime_analysis = analyze_runtime_logs(logs)

    details = dict(project.get("details") or {})
    production_url = str(details.get("production_url") or "")
    domain_health = check_domain_health(token, project_name=resolved_name, production_url=production_url or None)
    env_metadata = read_env_metadata(token, project_name=resolved_name) if operation in {
        "env_metadata",
        "live_diagnosis",
    } else {"ok": True, "skipped": True}

    evidence = {
        "ok": project.get("ok", False),
        "operation": operation,
        "project_name": resolved_name,
        "project": project,
        "deployments": deployments,
        "latest_deployment": latest,
        "failed_deployment": failed,
        "logs": logs,
        "build_analysis": build_analysis,
        "runtime_analysis": runtime_analysis,
        "domain_health": domain_health,
        "env_metadata": env_metadata,
    }

    from aethos_core.cross_provider_correlation.evidence_publisher import ingest_vercel_live_evidence

    github_correlation = ingest_vercel_live_evidence(session_id, evidence)
    evidence["github_correlation"] = github_correlation
    evidence["cross_provider_correlation"] = github_correlation
    return evidence


def _select_latest_deployment(deployments: dict[str, Any]) -> dict[str, Any] | None:
    rows = list(deployments.get("deployments") or [])
    return rows[0] if rows else None


def _select_failed_deployment(deployments: dict[str, Any]) -> dict[str, Any] | None:
    for row in deployments.get("deployments") or []:
        if str(row.get("state") or "").lower() in {"error", "failed", "canceled"}:
            return row
    return None

