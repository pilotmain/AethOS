# SPDX-License-Identifier: Apache-2.0
"""Local workspace API — readonly engineering intelligence."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["workspaces"])

_PATH_RX = re.compile(r"^[/~A-Za-z0-9._-]+$")


class RegisterWorkspaceIn(BaseModel):
    path: str = Field(min_length=1, max_length=512)
    name: str = Field(default="", max_length=120)


class RegisterGithubWorkspaceIn(BaseModel):
    repository: str = Field(min_length=3, max_length=200)
    branch: str = Field(default="", max_length=120)
    name: str = Field(default="", max_length=120)


class PortfolioRootIn(BaseModel):
    path: str = Field(min_length=1, max_length=512)
    max_scan_depth: int = Field(default=4, ge=1, le=8)
    max_projects: int = Field(default=100, ge=1, le=200)


class PortfolioDiscoverIn(BaseModel):
    auto_register: bool = False
    rescan: bool = True


@router.get("/workspaces/portfolio")
def get_portfolio_api() -> dict[str, Any]:
    from aethos_core.local_workspace.portfolio import get_portfolio_config

    return {"ok": True, "portfolio": get_portfolio_config()}


@router.post("/workspaces/portfolio")
def set_portfolio_root_api(body: PortfolioRootIn) -> dict[str, Any]:
    from aethos_core.local_workspace.portfolio import set_portfolio_root

    path = body.path.strip()
    if not _PATH_RX.match(path.replace(" ", "")):
        raise HTTPException(status_code=422, detail="Invalid portfolio root path.")
    try:
        portfolio = set_portfolio_root(
            path,
            max_scan_depth=body.max_scan_depth,
            max_projects=body.max_projects,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "portfolio": portfolio}


@router.post("/workspaces/portfolio/discover")
def discover_portfolio_api(body: PortfolioDiscoverIn) -> dict[str, Any]:
    from aethos_core.local_workspace.portfolio import discover_projects

    result = discover_projects(rescan=body.rescan, auto_register=body.auto_register)
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=str(result.get("detail") or "Discovery failed."))
    return {"ok": True, **result}


@router.get("/workspaces")
def list_workspaces_api() -> dict[str, Any]:
    from aethos_core.local_workspace.artifacts.store import list_workspace_artifacts
    from aethos_core.local_workspace.memory.engineering_memory import get_engineering_memory
    from aethos_core.local_workspace.portfolio import get_portfolio_config
    from aethos_core.production.deployment_mode import deployment_mode, is_hosted_deployment
    from aethos_core.remote_workspace.registry import merged_workspace_list

    return {
        "ok": True,
        "deployment_mode": deployment_mode(),
        "hosted": is_hosted_deployment(),
        "workspaces": merged_workspace_list(),
        "portfolio": get_portfolio_config(),
        "artifacts": list_workspace_artifacts(limit=20),
        "engineering_memory": get_engineering_memory(),
    }


@router.post("/workspaces/github/register")
def register_github_workspace_api(body: RegisterGithubWorkspaceIn) -> dict[str, Any]:
    from aethos_core.remote_workspace.registry import register_github_workspace

    try:
        record = register_github_workspace(
            body.repository,
            branch=body.branch or None,
            name=body.name or None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "workspace": record}


@router.get("/workspaces/artifacts")
def list_workspace_artifacts_api(limit: int = 40) -> dict[str, Any]:
    from aethos_core.local_workspace.artifacts.store import list_workspace_artifacts

    return {"ok": True, "artifacts": list_workspace_artifacts(limit=limit)}


@router.get("/workspaces/artifacts/{artifact_id}")
def get_workspace_artifact_api(artifact_id: str) -> dict[str, Any]:
    from aethos_core.local_workspace.artifacts.store import get_workspace_artifact

    row = get_workspace_artifact(artifact_id)
    if not row:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"ok": True, "artifact": row}


@router.post("/workspaces/register")
def register_workspace_api(body: RegisterWorkspaceIn) -> dict[str, Any]:
    from aethos_core.local_workspace.artifacts.store import store_workspace_artifact
    from aethos_core.local_workspace.registry import register_workspace
    from aethos_core.local_workspace.readonly.actions import run_workspace_scan

    path = body.path.strip()
    if not _PATH_RX.match(path.replace(" ", "")):
        raise HTTPException(status_code=422, detail="Invalid workspace path.")
    try:
        record = register_workspace(path=path, name=body.name or None)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    scan = run_workspace_scan(Path(record["path"]), workspace_id=record["workspace_id"])
    artifact = store_workspace_artifact(
        artifact_type="workspace_registration",
        workspace_id=record["workspace_id"],
        repo_path=record["path"],
        payload={"workspace": record, "scan": scan.get("scan")},
        summary=f"Registered workspace {record.get('name')}",
    )
    return {"ok": True, "workspace": record, "scan": scan, "artifact": artifact}


@router.get("/workspaces/context")
def workspace_context_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.chat.engineering_intelligence import build_engineering_context

    return build_engineering_context(session_id=session_id)


def _resolve_workspace_row(workspace_id: str) -> dict[str, Any] | None:
    from aethos_core.local_workspace.registry import get_workspace
    from aethos_core.remote_workspace.registry import list_github_workspaces

    row = _resolve_workspace_row(workspace_id)
    if row:
        return row
    for gh in list_github_workspaces():
        if str(gh.get("workspace_id")) == workspace_id:
            return gh
    return None


@router.get("/workspaces/{workspace_id}")
def get_workspace_api(workspace_id: str) -> dict[str, Any]:
    row = _resolve_workspace_row(workspace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"ok": True, "workspace": row}


@router.get("/workspaces/{workspace_id}/status")
def workspace_status_api(workspace_id: str) -> dict[str, Any]:
    from aethos_core.local_workspace.readonly.actions import run_git_status_report

    row = _resolve_workspace_row(workspace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    result = run_git_status_report(hint=row.get("name") or str(row.get("path")))
    return {"ok": True, "workspace": row, **result}


@router.get("/workspaces/{workspace_id}/architecture")
def workspace_architecture_api(workspace_id: str) -> dict[str, Any]:
    from aethos_core.local_workspace.readonly.actions import run_architecture_report

    row = _resolve_workspace_row(workspace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    result = run_architecture_report(hint=row.get("name") or str(row.get("path")))
    return {"ok": True, "workspace": row, **result}


@router.get("/workspaces/{workspace_id}/dependencies")
def workspace_dependencies_api(workspace_id: str) -> dict[str, Any]:
    from aethos_core.local_workspace.readonly.actions import run_dependency_report

    row = _resolve_workspace_row(workspace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    result = run_dependency_report(hint=row.get("name") or str(row.get("path")))
    return {"ok": True, "workspace": row, **result}


@router.get("/workspaces/{workspace_id}/tests")
def workspace_tests_api(workspace_id: str) -> dict[str, Any]:
    from aethos_core.local_workspace.analysis.diagnostics import analyze_test_state
    row = _resolve_workspace_row(workspace_id)
    if not row:
        raise HTTPException(status_code=404, detail="Workspace not found")
    analysis = analyze_test_state(Path(str(row["path"])))
    return {"ok": True, "workspace": row, "tests": analysis}
