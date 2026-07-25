# SPDX-License-Identifier: Apache-2.0
"""Engineering execution — bounded mutation after approval."""

from __future__ import annotations

from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.engineering.diff_intelligence import analyze_patch_diffs
from aethos_core.engineering.governance.engineering_rollback import create_rollback_snapshot, rollback_plan_for_execution
from aethos_core.engineering.governance.engineering_scope import EngineeringRiskTier, execution_allowed
from aethos_core.engineering.governance.engineering_validation import run_engineering_validation_step
from aethos_core.engineering.patch_runtime.patch_artifacts import store_patch_artifact
from aethos_core.engineering.patch_runtime.patch_generator import apply_patches_to_workspace
from aethos_core.engineering.patch_runtime.patch_validator import validate_patches
from aethos_core.engineering.pr_drafts import build_governed_pr_draft, store_pr_draft
from aethos_core.local_workspace.mutation_workspace import create_mutation_workspace


def run_engineering_execution(
    *,
    preflight: dict[str, Any],
    repo: Path,
    approved: bool = False,
) -> dict[str, Any]:
    """Execute governed engineering mutation in sandbox — never auto-merge."""
    if not approved:
        return {
            "ok": False,
            "status": "approval_required",
            "error": "Engineering execution requires explicit approval.",
            "execution_enabled": False,
        }

    tier = EngineeringRiskTier(preflight.get("risk_tier") or EngineeringRiskTier.E1_PROPOSAL.value)
    if not execution_allowed(tier):
        return {
            "ok": False,
            "status": "tier_blocked",
            "error": f"Execution not allowed for tier {tier.value}",
            "execution_enabled": False,
        }

    patch = preflight.get("patch_proposal") or {}
    task = preflight.get("task") or {}
    files = patch.get("files_affected") or []
    patches = patch.get("patches") or []
    research_context = _maybe_research_context(preflight, task)

    workspace = create_mutation_workspace(repo_path=repo, file_scope=files)
    snapshot = create_rollback_snapshot(
        workspace_id=workspace["workspace_id"],
        branch=workspace["branch"],
        files_modified=[],
        sandbox_path=workspace.get("sandbox_path"),
    )
    workspace["rollback_snapshot"] = snapshot["snapshot_id"]
    execution_id = f"exe-{uuid4().hex[:12]}"

    validation = {"validation_status": "validation_pending", "ok": True}
    apply_result: dict[str, Any] = {"ok": True, "applied": []}

    if patches:
        val = validate_patches(repo, patches)
        if not val.get("ok"):
            return _fail_execution(
                preflight=preflight,
                execution_id=execution_id,
                workspace=workspace,
                snapshot=snapshot,
                error="patch_validation_failed",
                detail=val,
            )
        apply_result = apply_patches_to_workspace(workspace, patches)
        workspace = apply_result.get("workspace") or workspace
        snapshot = create_rollback_snapshot(
            workspace_id=workspace["workspace_id"],
            branch=workspace["branch"],
            files_modified=workspace.get("files_modified") or [],
            sandbox_path=workspace.get("sandbox_path"),
        )
        workspace["rollback_snapshot"] = snapshot["snapshot_id"]

    unified = patch.get("unified_diffs") or []
    diff_intel = patch.get("diff_intelligence") or analyze_patch_diffs(
        unified_diffs=unified, blast_radius=patch.get("blast_radius"), task=task
    )

    patch_art = store_patch_artifact(
        preflight_id=str(preflight.get("preflight_id") or ""),
        execution_id=execution_id,
        payload={
            "patches": patches,
            "unified_diffs": unified,
            "diff_intelligence": diff_intel,
            "apply_result": apply_result,
            "research_context": research_context,
        },
    )

    if apply_result.get("applied"):
        validation = run_engineering_validation_step(
            repo,
            patch_plan=preflight.get("patch_plan"),
            workspace=workspace,
        )

    pr_draft = build_governed_pr_draft(
        preflight=preflight,
        execution={"execution_id": execution_id, "workspace": workspace, "validation": validation},
        diff_intel=diff_intel,
        research_context=research_context,
    )
    pr_draft = store_pr_draft(preflight_id=str(preflight.get("preflight_id") or ""), draft=pr_draft)

    ok = bool(apply_result.get("ok")) and validation.get("ok", False)
    result = {
        "ok": ok,
        "execution_id": execution_id,
        "status": "engineering_execution_complete" if ok else "validation_failed",
        "workspace_id": workspace["workspace_id"],
        "branch": workspace["branch"],
        "files_modified": workspace.get("files_modified") or apply_result.get("applied") or [],
        "diff_size": workspace.get("diff_size", 0),
        "rollback_snapshot": snapshot["snapshot_id"],
        "rollback_plan": rollback_plan_for_execution(
            {"rollback_snapshot": snapshot["snapshot_id"], "branch": workspace["branch"]}
        ),
        "validation": validation,
        "pr_draft": pr_draft,
        "patch_artifact_id": patch_art.get("artifact_id"),
        "diff_intelligence": diff_intel,
        "research_context": research_context,
        "audit": {
            "at": time(),
            "preflight_id": preflight.get("preflight_id"),
            "execution_id": execution_id,
            "approved": True,
            "auto_merge": False,
        },
        "execution_enabled": False,
        "merge_enabled": False,
    }
    from aethos_core.engineering.engineering_memory import record_engineering_outcome
    from aethos_core.engineering.governance.engineering_audit import record_execution

    record_engineering_outcome(
        preflight_id=str(preflight.get("preflight_id") or ""),
        execution_id=execution_id,
        status=result["status"],
        validation_status=str(validation.get("validation_status") or ""),
        task_kind=str(task.get("kind") or ""),
    )
    record_execution(result)
    return result


def _maybe_research_context(preflight: dict[str, Any], task: dict[str, Any]) -> dict[str, Any] | None:
    kind = str(task.get("kind") or "")
    if kind not in ("dependency_modernization", "deployment_diagnostics"):
        return None
    try:
        from aethos_core.research.operational_research import research_context_for_prompt

        return research_context_for_prompt(str(preflight.get("user_request") or task.get("title") or ""))
    except Exception:
        return None


def _fail_execution(
    *,
    preflight: dict[str, Any],
    execution_id: str,
    workspace: dict[str, Any],
    snapshot: dict[str, Any],
    error: str,
    detail: Any,
) -> dict[str, Any]:
    return {
        "ok": False,
        "execution_id": execution_id,
        "status": error,
        "error": error,
        "detail": detail,
        "workspace_id": workspace.get("workspace_id"),
        "rollback_snapshot": snapshot.get("snapshot_id"),
        "merge_enabled": False,
    }


def get_execution_state(execution_id: str) -> dict[str, Any] | None:
    from aethos_core.engineering.governance.engineering_audit import get_execution_record

    return get_execution_record(execution_id)
