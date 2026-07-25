# SPDX-License-Identifier: Apache-2.0
"""Dispatch GitHub Actions workflows via workflow_dispatch."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.github.api_client import parse_owner_repo, request_github


def dispatch_workflow(
    token: str,
    *,
    repository: str,
    workflow_id: str | int,
    ref: str = "main",
    inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    owner, repo = parse_owner_repo(repository)
    if not owner or not repo:
        return {"ok": False, "detail": f"Repository `{repository}` could not be parsed."}
    path = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
    body: dict[str, Any] = {"ref": ref}
    if inputs:
        body["inputs"] = inputs
    result = request_github(token, "POST", path, json_body=body)
    http_status = result.get("http_status")
    if result.get("ok") or http_status in (201, 204):
        return {
            "ok": True,
            "detail": f"Workflow `{workflow_id}` dispatch requested on `{repository}` @ `{ref}`.",
            "repository": f"{owner}/{repo}",
            "workflow_id": workflow_id,
            "ref": ref,
            "http_status": http_status or 204,
            "operation": "workflow_dispatch",
        }
    return {
        "ok": False,
        "detail": str(result.get("error") or "workflow dispatch failed."),
        "http_status": http_status,
        "operation": "workflow_dispatch",
    }
