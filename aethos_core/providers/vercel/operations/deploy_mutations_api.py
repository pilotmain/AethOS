# SPDX-License-Identifier: Apache-2.0
"""Vercel governed deploy mutations — promote, rollback, deploy-from-git (approval-gated).

Real Vercel REST calls; governance/approval is enforced by the adapter/execution layer above.
Each returns a normalized {ok, detail, ...} shape. Rollback is implemented as promoting the
previous READY production deployment (the correct, well-documented path) rather than a
provider-specific rollback endpoint.
"""

from __future__ import annotations

from typing import Any

import httpx

from aethos_core.providers.vercel.api_client import VERCEL_API_BASE, find_project_by_name, list_deployments
from aethos_core.security.secret_redaction import redact_text


def _project_id(token: str, target_name: str, team_id: str | None) -> tuple[str | None, dict[str, Any] | None]:
    project = find_project_by_name(token, target_name, team_id=team_id)
    if not project:
        return None, {"ok": False, "detail": f"Vercel project `{target_name}` not found.", "failure_classification": "target_unresolved"}
    pid = str(project.get("id") or "")
    if not pid:
        return None, {"ok": False, "detail": "Project id unavailable.", "failure_classification": "target_unresolved"}
    return pid, None


def _promote(token: str, *, project_id: str, deployment_id: str, team_id: str | None) -> dict[str, Any]:
    params = {"teamId": team_id} if team_id else {}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(
                f"{VERCEL_API_BASE}/v10/projects/{project_id}/promote/{deployment_id}",
                headers=headers,
                params=params,
            )
        if r.status_code >= 400:
            return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}"), "http_status": r.status_code}
        return {"ok": True, "project_id": project_id, "deployment_id": deployment_id, "http_status": r.status_code}
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc)), "failure_classification": "provider_unreachable"}


def promote_deployment(token: str, *, target_name: str, deployment_id: str, team_id: str | None = None) -> dict[str, Any]:
    pid, err = _project_id(token, target_name, team_id)
    if err:
        return err
    if not deployment_id:
        return {"ok": False, "detail": "deployment_id required to promote.", "failure_classification": "invalid_request"}
    res = _promote(token, project_id=pid, deployment_id=deployment_id, team_id=team_id)
    if res.get("ok"):
        res |= {"operation": "promote_deployment", "detail": f"Promoted deployment `{deployment_id}` to production for `{target_name}`."}
    return res


def rollback(token: str, *, target_name: str, team_id: str | None = None) -> dict[str, Any]:
    """Roll back production by promoting the previous READY production deployment."""
    pid, err = _project_id(token, target_name, team_id)
    if err:
        return err
    deployments = list_deployments(token, project_id=pid, team_id=team_id, limit=30)
    prod_ready = [
        d for d in deployments
        if str(d.get("target")) == "production" and str(d.get("readyState") or d.get("state")) in ("READY", "ready")
    ]
    if len(prod_ready) < 2:
        return {"ok": False, "detail": "No previous production deployment to roll back to.", "failure_classification": "no_rollback_target"}
    previous = prod_ready[1]  # [0] is current production, [1] is the prior one
    dep_id = str(previous.get("uid") or previous.get("id") or "")
    if not dep_id:
        return {"ok": False, "detail": "Previous deployment id unavailable.", "failure_classification": "no_rollback_target"}
    res = _promote(token, project_id=pid, deployment_id=dep_id, team_id=team_id)
    if res.get("ok"):
        res |= {"operation": "rollback", "detail": f"Rolled back `{target_name}` to previous deployment `{dep_id}`."}
    return res


def deploy_from_git(token: str, *, target_name: str, ref: str | None = None, team_id: str | None = None) -> dict[str, Any]:
    """Trigger a production deployment from the project's connected git repo (optional ref)."""
    pid, err = _project_id(token, target_name, team_id)
    if err:
        return err
    params = {"teamId": team_id} if team_id else {}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    body: dict[str, Any] = {"name": target_name, "project": pid, "target": "production"}
    if ref:
        body["gitSource"] = {"ref": ref}
    try:
        with httpx.Client(timeout=45.0) as client:
            r = client.post(f"{VERCEL_API_BASE}/v13/deployments", headers=headers, params=params, json=body)
        if r.status_code >= 400:
            return {"ok": False, "detail": redact_text(r.text[:240] or f"HTTP {r.status_code}"), "http_status": r.status_code}
        data = r.json() if r.content else {}
        return {
            "ok": True,
            "operation": "deploy_from_git",
            "project_id": pid,
            "deployment_id": str(data.get("id") or "") or None,
            "detail": f"Triggered git deployment for `{target_name}`" + (f" (ref `{ref}`)." if ref else "."),
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": redact_text(str(exc)), "failure_classification": "provider_unreachable"}
