# SPDX-License-Identifier: Apache-2.0
"""Engineering execution API — governed patch lifecycle."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["engineering"])


class EngineeringPreflightRequest(BaseModel):
    user_request: str
    workspace_hint: str | None = None
    session_id: str = "default"


class EngineeringDenyRequest(BaseModel):
    reason: str = ""


@router.post("/engineering/preflight")
def engineering_preflight_api(body: EngineeringPreflightRequest) -> dict[str, Any]:
    from aethos_core.engineering.governance.engineering_preflight import run_and_record_engineering_preflight
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint

    repo = _repo_from_hint(body.workspace_hint or "aethos", session_id=body.session_id)
    result = run_and_record_engineering_preflight(
        user_request=body.user_request,
        repo=repo,
        workspace_hint=body.workspace_hint,
        session_id=body.session_id,
        source="api",
    )
    return {"ok": True, "preflight": result}


@router.get("/engineering/preflights")
def list_engineering_preflights_api() -> dict[str, Any]:
    from aethos_core.engineering.governance.engineering_preflight_store import (
        list_all_preflights,
        list_pending_preflights,
    )

    return {
        "ok": True,
        "pending": list_pending_preflights(),
        "all": list_all_preflights(),
    }


@router.post("/engineering/preflights/{preflight_id}/approve")
def approve_engineering_preflight_api(preflight_id: str) -> dict[str, Any]:
    from aethos_core.engineering.governance.engineering_preflight_store import approve_preflight

    result = approve_preflight(preflight_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "approval_failed")
    return result


@router.post("/engineering/preflights/{preflight_id}/deny")
def deny_engineering_preflight_api(preflight_id: str, body: EngineeringDenyRequest | None = None) -> dict[str, Any]:
    from aethos_core.engineering.governance.engineering_preflight_store import deny_preflight

    result = deny_preflight(preflight_id, reason=(body.reason if body else ""))
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "deny_failed")
    return result


@router.get("/engineering/state")
def engineering_state_api() -> dict[str, Any]:
    from aethos_core.engineering.engineering_memory import engineering_memory_snapshot
    from aethos_core.engineering.governance.engineering_audit import list_execution_records
    from aethos_core.engineering.governance.engineering_preflight_store import list_all_preflights, list_pending_preflights
    from aethos_core.engineering.governance.engineering_rollback import list_rollback_snapshots
    from aethos_core.engineering.patch_runtime.patch_artifacts import list_patch_artifacts
    from aethos_core.engineering.pr_drafts import list_pr_drafts
    from aethos_core.local_workspace.mutation_workspace import list_mutation_workspaces
    from aethos_core.operations.reality_loop import run_reality_loop_scan

    all_preflights = list_all_preflights()
    approved = [p for p in all_preflights if p.get("approved")]
    executions = list_execution_records(limit=10)
    validations = [
        {
            "preflight_id": ex.get("audit", {}).get("preflight_id") or ex.get("preflight_id"),
            "execution_id": ex.get("execution_id"),
            "validation": ex.get("validation"),
        }
        for ex in executions
        if ex.get("validation")
    ]

    return {
        "ok": True,
        "pending_preflights": list_pending_preflights(),
        "approved_preflights": approved,
        "mutation_workspaces": list_mutation_workspaces(limit=10),
        "executions": executions,
        "pr_drafts": list_pr_drafts(limit=10) or [p.get("execution", {}).get("pr_draft") for p in approved if p.get("execution", {}).get("pr_draft")],
        "patch_artifacts": list_patch_artifacts(limit=10),
        "validations": validations,
        "rollback_snapshots": list_rollback_snapshots(limit=10),
        "engineering_memory": engineering_memory_snapshot(),
        "reality_loop": run_reality_loop_scan(),
    }


@router.get("/engineering/diffs/{artifact_id}")
def engineering_diff_api(artifact_id: str) -> dict[str, Any]:
    from aethos_core.engineering.patch_runtime.patch_artifacts import get_patch_artifact

    artifact = get_patch_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="diff_not_found")
    return {"ok": True, "artifact": artifact}


@router.get("/engineering/pr-drafts")
def engineering_pr_drafts_api() -> dict[str, Any]:
    from aethos_core.engineering.pr_drafts import list_pr_drafts

    return {"ok": True, "drafts": list_pr_drafts(limit=30)}


@router.get("/engineering/validations")
def engineering_validations_api() -> dict[str, Any]:
    from aethos_core.engineering.governance.engineering_audit import list_execution_records

    rows = []
    for ex in list_execution_records(limit=30):
        if ex.get("validation"):
            rows.append(
                {
                    "execution_id": ex.get("execution_id"),
                    "preflight_id": ex.get("audit", {}).get("preflight_id"),
                    "validation": ex.get("validation"),
                    "status": ex.get("status"),
                }
            )
    return {"ok": True, "validations": rows}


@router.get("/engineering/rollback-snapshots")
def engineering_rollback_snapshots_api() -> dict[str, Any]:
    from aethos_core.engineering.governance.engineering_rollback import list_rollback_snapshots

    return {"ok": True, "snapshots": list_rollback_snapshots(limit=30)}



@router.get("/engineering/reality-loop")
def reality_loop_api() -> dict[str, Any]:
    from aethos_core.operations.reality_loop import format_reality_loop_report, run_reality_loop_scan

    scan = run_reality_loop_scan()
    return {"ok": True, "scan": scan, "report": format_reality_loop_report(scan)}
