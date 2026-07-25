# SPDX-License-Identifier: Apache-2.0
"""Governed redeploy step for provider E2E orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.provider_e2e_orchestration.job_model import ProviderE2EJobModel


def execute_redeploy(model: ProviderE2EJobModel, *, params: dict[str, Any]) -> dict[str, Any]:
    if model.deploy_action == "none":
        return {"ok": True, "skipped": True, "detail": "Redeploy not requested."}

    if model.provider == "railway":
        return _redeploy_railway(model, params)
    if model.provider == "vercel":
        return _redeploy_vercel(model, params)
    return {"ok": False, "detail": f"Unsupported provider `{model.provider}`."}


def _redeploy_railway(model: ProviderE2EJobModel, params: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.railway.mutations import execute_railway_mutation
    from aethos_core.providers.railway.target_resolver import ProviderTarget

    target = ProviderTarget(
        provider="railway",
        service_name=model.service_name,
        project_name=model.project_name,
        environment=model.environment,
        service_id=model.service_id or None,
        resolved=True,
    )
    exec_params = {
        "target_name": model.service_name,
        "target": {
            "service_name": model.service_name,
            "project_name": model.project_name,
            "environment": model.environment,
            "service_id": model.service_id,
            "resolved": True,
        },
        "mutation_execution_approved": True,
        "approval_id": params.get("approval_id"),
    }
    result = execute_railway_mutation(operation="redeploy", params=exec_params, request_id=str(params.get("approval_id") or "e2e"))
    deployment_id = None
    if isinstance(result, dict):
        deployment_id = (
            result.get("deployment_id")
            or (result.get("provider_result") or {}).get("deployment_id")
            or (result.get("railway_mutation_result") or {}).get("deployment_id")
        )
    return {
        "ok": bool(result.get("ok")) if isinstance(result, dict) else False,
        "detail": str(result.get("detail") or "") if isinstance(result, dict) else "redeploy failed",
        "deployment_id": deployment_id,
        "service_id": result.get("service_id") if isinstance(result, dict) else model.service_id,
        "operation": "redeploy",
    }


def _redeploy_vercel(model: ProviderE2EJobModel, params: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.vercel.auth import VercelAuthAdapter
    from aethos_core.providers.vercel.operations.mutations_api import deploy_project_from_github, redeploy_project

    credential_id = model.credential_id or str(params.get("credential_id") or "")
    token = VercelAuthAdapter().get_api_token(credential_id) if credential_id else None
    if not token:
        auth = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
        credential_id = str(auth.get("credential_id") or "")
        token = VercelAuthAdapter().get_api_token(credential_id) if credential_id else None
    if not token:
        return {"ok": False, "detail": "Vercel token unavailable for redeploy."}

    repo = str(params.get("referenced_github_repo") or "")
    github_repo_id = params.get("github_repo_id")
    branch = str(params.get("branch") or "main")
    if params.get("greenfield") and repo:
        result = deploy_project_from_github(
            token,
            target_name=model.project_name,
            repo=repo,
            ref=branch,
            github_repo_id=github_repo_id,
        )
    else:
        result = redeploy_project(token, target_name=model.project_name)
    return {
        "ok": bool(result.get("ok")),
        "detail": str(result.get("detail") or ""),
        "deployment_id": result.get("deployment_id"),
        "deployment_url": result.get("deployment_url"),
        "project_id": result.get("project_id") or model.project_id,
        "operation": result.get("operation") or "redeploy",
    }
