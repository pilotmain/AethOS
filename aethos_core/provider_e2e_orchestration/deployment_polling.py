# SPDX-License-Identifier: Apache-2.0
"""Deployment status polling for provider E2E orchestration."""

from __future__ import annotations

import time
from typing import Any, Literal

from aethos_core.config import get_settings
from aethos_core.provider_e2e_orchestration.job_model import ProviderE2EJobModel

PollState = Literal["pending", "building", "deploying", "ready", "failed", "timed_out"]


def poll_deployment_status(
    model: ProviderE2EJobModel,
    *,
    deployment_id: str | None,
    params: dict[str, Any],
) -> dict[str, Any]:
    settings = get_settings()
    interval = float(getattr(settings, "provider_e2e_poll_interval_sec", 0.5) or 0.5)
    max_attempts = int(getattr(settings, "provider_e2e_poll_max_attempts", 20) or 20)
    timeline: list[dict[str, Any]] = []

    if not deployment_id:
        return {
            "ok": False,
            "final_state": "failed",
            "detail": "No deployment ID to poll.",
            "timeline": timeline,
        }

    state: PollState = "pending"
    for attempt in range(max_attempts):
        snapshot = _fetch_status(model, deployment_id=deployment_id, params=params)
        raw = str(snapshot.get("raw_state") or "unknown").lower()
        state = _map_state(raw)
        timeline.append(
            {
                "attempt": attempt + 1,
                "at": time.time(),
                "raw_state": raw,
                "mapped_state": state,
                "url": snapshot.get("url"),
            }
        )
        if state == "ready":
            return {
                "ok": True,
                "final_state": "ready",
                "deployment_id": deployment_id,
                "deployment_url": snapshot.get("url"),
                "timeline": timeline,
                "detail": "Deployment reached ready state.",
            }
        if state == "failed":
            return {
                "ok": False,
                "final_state": "failed",
                "deployment_id": deployment_id,
                "timeline": timeline,
                "detail": str(snapshot.get("error") or "Deployment failed."),
            }
        time.sleep(interval)

    return {
        "ok": False,
        "final_state": "timed_out",
        "deployment_id": deployment_id,
        "timeline": timeline,
        "detail": f"Polling timed out after {max_attempts} attempts.",
    }


def _map_state(raw: str) -> PollState:
    if raw in {"success", "ready", "active", "completed"}:
        return "ready"
    if raw in {"failed", "crashed", "error", "cancelled", "canceled"}:
        return "failed"
    if raw in {"building", "build", "queued", "initializing"}:
        return "building"
    if raw in {"deploying", "deploy", "running", "restarting"}:
        return "deploying"
    if raw in {"pending", "waiting"}:
        return "pending"
    return "deploying"


def _fetch_status(model: ProviderE2EJobModel, *, deployment_id: str, params: dict[str, Any]) -> dict[str, Any]:
    if model.provider == "railway":
        return _railway_status(model, deployment_id=deployment_id)
    if model.provider == "vercel":
        return _vercel_status(model, deployment_id=deployment_id, params=params)
    return {"raw_state": "unknown"}


def _railway_status(model: ProviderE2EJobModel, *, deployment_id: str) -> dict[str, Any]:
    from aethos_core.providers.railway.api_client import graphql_query, list_service_deployments
    from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

    token, _, _ = resolve_railway_mutation_credentials()
    if not token:
        return {"raw_state": "failed", "error": "missing token"}

    service_id = model.service_id
    if not service_id and model.service_name:
        from aethos_core.providers.railway.api_client import find_service_by_name

        svc = find_service_by_name(token, model.service_name)
        service_id = str((svc or {}).get("service_id") or "")

    if service_id:
        deployments = list_service_deployments(token, service_id=service_id, limit=5)
        for dep in deployments:
            if str(dep.get("id") or "") == deployment_id:
                return {
                    "raw_state": str(dep.get("state") or dep.get("status") or "unknown"),
                    "url": dep.get("url"),
                }

    out = graphql_query(
        token,
        "query Deployment($id: String!) { deployment(id: $id) { id status url } }",
        {"id": deployment_id},
    )
    if out.get("ok"):
        dep = ((out.get("data") or {}).get("deployment")) or {}
        return {"raw_state": str(dep.get("status") or "unknown"), "url": dep.get("url")}
    return {"raw_state": "unknown"}


def _vercel_status(model: ProviderE2EJobModel, *, deployment_id: str, params: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.providers.vercel.api_client import VERCEL_API_BASE, parse_deployment_record
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    import httpx

    credential_id = model.credential_id or str(params.get("credential_id") or "")
    token = VercelAuthAdapter().get_api_token(credential_id) if credential_id else None
    if not token:
        auth = VercelAuthAdapter().resolve_best_auth_method(operation="read_projects")
        credential_id = str(auth.get("credential_id") or "")
        token = VercelAuthAdapter().get_api_token(credential_id) if credential_id else None
    if not token:
        return {"raw_state": "failed", "error": "missing token"}

    headers = {"Authorization": f"Bearer {token}"}
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(f"{VERCEL_API_BASE}/v13/deployments/{deployment_id}", headers=headers)
        if r.status_code >= 400:
            return {"raw_state": "failed", "error": r.text[:120]}
        data = parse_deployment_record(r.json() if r.content else {})
        url = data.get("url") or ""
        if url and not str(url).startswith("http"):
            url = f"https://{url}"
        return {"raw_state": str(data.get("state") or "unknown"), "url": url, "error": data.get("error_message")}
    except httpx.HTTPError as exc:
        return {"raw_state": "failed", "error": str(exc)}
