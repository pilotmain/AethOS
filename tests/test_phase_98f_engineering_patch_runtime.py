# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8F — Governed patch runtime, PR drafts, diff intelligence."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aethos_core.engineering.diff_intelligence import analyze_patch_diffs
from aethos_core.engineering.engineering_memory import clear_engineering_memory_for_tests, engineering_memory_snapshot
from aethos_core.engineering.governance.engineering_execution import run_engineering_execution
from aethos_core.engineering.governance.engineering_preflight import run_engineering_preflight
from aethos_core.engineering.governance.engineering_preflight_store import (
    approve_preflight,
    clear_engineering_preflights_for_tests,
    record_engineering_preflight,
)
from aethos_core.engineering.governance.engineering_rollback import clear_rollback_snapshots_for_tests, list_rollback_snapshots
from aethos_core.engineering.governance.engineering_scope import EngineeringRiskTier, execution_allowed
from aethos_core.engineering.governance.engineering_validation import run_engineering_validation_step
from aethos_core.engineering.patch_engine import generate_patch_proposal
from aethos_core.engineering.patch_runtime.patch_artifacts import clear_patch_artifacts_for_tests, get_patch_artifact
from aethos_core.engineering.patch_runtime.patch_generator import apply_patches_to_workspace, generate_governed_patches
from aethos_core.engineering.patch_runtime.patch_revert import revert_workspace_from_snapshot
from aethos_core.engineering.patch_runtime.patch_scope import validate_patch_scope
from aethos_core.engineering.pr_drafts import build_governed_pr_draft, clear_pr_drafts_for_tests, list_pr_drafts, store_pr_draft
from aethos_core.engineering.task_intake import intake_engineering_task
from aethos_core.local_workspace.mutation_workspace import create_mutation_workspace


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_engineering_preflights_for_tests()
    clear_patch_artifacts_for_tests()
    clear_pr_drafts_for_tests()
    clear_rollback_snapshots_for_tests()
    clear_engineering_memory_for_tests()
    yield
    clear_engineering_preflights_for_tests()
    clear_patch_artifacts_for_tests()
    clear_pr_drafts_for_tests()
    clear_rollback_snapshots_for_tests()
    clear_engineering_memory_for_tests()


def _workflow_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    path = repo / "aethos_core/providers/github/shared/workflow_resolution.py"
    path.parent.mkdir(parents=True)
    path.write_text("RESOLUTION = 'stub'\n")
    return repo


def test_preflight_e2_tier_for_workflow_fix(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    preflight = run_engineering_preflight(
        user_request="Fix the GitHub workflow rerun issue in AethOS",
        repo=repo,
    )
    assert preflight["risk_tier"] == EngineeringRiskTier.E2_BRANCH_DIFF.value
    proposal = preflight["patch_proposal"]
    assert proposal.get("unified_diffs")
    assert proposal.get("patches")
    assert preflight["execution_enabled"] is False


def test_scoped_patch_blocks_env(tmp_path: Path):
    scope = validate_patch_scope(
        allowed_files=["src/app.py"],
        requested_files=[".env", "src/app.py"],
        user_request="update config",
    )
    assert scope["ok"] is False
    assert ".env" in scope["blocked_paths"][0] or any(".env" in b for b in scope["blocked_paths"])


def test_generate_governed_patches_real_diff(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    task = intake_engineering_task("Fix the GitHub workflow rerun issue in AethOS", repo=repo)
    generated = generate_governed_patches(repo, user_request="fix workflow rerun", task=task)
    assert generated["ok"] is True
    assert generated["unified_diffs"]
    assert "GOVERNED_RERUN_RESOLUTION_SUBSTRATE" in generated["patches"][0]["new_content"]


def test_sandbox_isolation_no_source_mutation(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    source = repo / "aethos_core/providers/github/shared/workflow_resolution.py"
    original = source.read_text()
    task = intake_engineering_task("Fix workflow rerun", repo=repo)
    generated = generate_governed_patches(repo, user_request="fix", task=task)
    ws = create_mutation_workspace(repo_path=repo, file_scope=[generated["files_patched"][0]])
    apply_patches_to_workspace(ws, generated["patches"])
    assert source.read_text() == original
    sandbox_file = Path(ws["sandbox_path"]) / generated["files_patched"][0]
    assert "GOVERNED_RERUN_RESOLUTION_SUBSTRATE" in sandbox_file.read_text()


def test_diff_intelligence_detects_api_change():
    diffs = [
        {
            "file": "aethos_core/foo.py",
            "diff": "@@\n-old\n+def new_api():\n+    pass\n",
            "lines_changed": 3,
        }
    ]
    intel = analyze_patch_diffs(unified_diffs=diffs, task={"kind": "workflow_fix"})
    assert intel["api_contract_changes"] is True
    assert intel["severity"] in ("medium", "high", "low")


def test_validation_blocks_unrestricted_shell(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    result = run_engineering_validation_step(
        repo,
        patch_plan={"validation_steps": ["unrestricted shell", "arbitrary bash"]},
    )
    assert result["ok"] is False
    assert result.get("error") == "unrestricted_shell_blocked"


def test_pr_draft_governance_no_auto_merge(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    preflight = run_engineering_preflight(user_request="Fix workflow rerun", repo=repo)
    draft = build_governed_pr_draft(
        preflight=preflight,
        execution={"validation": {"validation_status": "validated", "ok": True}},
        diff_intel=preflight["patch_proposal"].get("diff_intelligence"),
    )
    assert draft["auto_merge"] is False
    assert draft["merge_enabled"] is False
    assert "Human merge required" in draft["governance_statement"]


@patch("aethos_core.engineering.governance.engineering_execution.run_engineering_validation_step")
def test_e2_execution_applies_patch_in_sandbox(mock_val, tmp_path: Path):
    mock_val.return_value = {"ok": True, "validation_status": "validated", "pass_count": 2, "fail_count": 0}
    repo = _workflow_repo(tmp_path)
    preflight = run_engineering_preflight(user_request="Fix the GitHub workflow rerun issue in AethOS", repo=repo)
    execution = run_engineering_execution(preflight=preflight, repo=repo, approved=True)
    assert execution["ok"] is True
    assert execution.get("merge_enabled") is False
    assert execution.get("audit", {}).get("auto_merge") is False
    assert execution.get("files_modified")
    assert execution.get("rollback_snapshot")
    assert execution.get("patch_artifact_id")
    artifact = get_patch_artifact(execution["patch_artifact_id"])
    assert artifact and artifact.get("unified_diffs")
    assert list_rollback_snapshots()


def test_rollback_snapshot_restore(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    task = intake_engineering_task("Fix workflow rerun", repo=repo)
    generated = generate_governed_patches(repo, user_request="fix", task=task)
    ws = create_mutation_workspace(repo_path=repo, file_scope=generated["files_patched"])
    apply_patches_to_workspace(ws, generated["patches"])
    from aethos_core.engineering.governance.engineering_rollback import create_rollback_snapshot

    snap = create_rollback_snapshot(
        workspace_id=ws["workspace_id"],
        branch=ws["branch"],
        files_modified=ws["files_modified"],
        sandbox_path=ws["sandbox_path"],
    )
    sandbox_file = Path(ws["sandbox_path"]) / generated["files_patched"][0]
    assert "GOVERNED" in sandbox_file.read_text()
    sandbox_file.write_text("corrupted\n")
    restored = revert_workspace_from_snapshot(snap["snapshot_id"])
    assert restored["ok"] is True
    assert "GOVERNED" in sandbox_file.read_text()



@patch("aethos_core.engineering.governance.engineering_execution.run_engineering_validation_step")
@patch("aethos_core.local_workspace.readonly.actions._repo_from_hint")
def test_approve_preflight_full_lifecycle(mock_repo, mock_val, tmp_path: Path):
    mock_val.return_value = {"ok": True, "validation_status": "validated", "pass_count": 1, "fail_count": 0}
    repo = _workflow_repo(tmp_path)
    mock_repo.return_value = repo
    preflight = run_engineering_preflight(
        user_request="Fix the GitHub workflow rerun issue in AethOS",
        repo=repo,
        persist=False,
    )
    record_engineering_preflight(
        preflight=preflight,
        user_request="Fix the GitHub workflow rerun issue in AethOS",
    )
    result = approve_preflight(preflight["preflight_id"])
    assert result["ok"] is True
    execution = result["execution"]
    assert execution.get("proposal_only") is not True
    assert execution.get("pr_draft")
    assert list_pr_drafts()


def test_execution_requires_approval(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    preflight = run_engineering_preflight(user_request="Fix workflow rerun", repo=repo)
    denied = run_engineering_execution(preflight=preflight, repo=repo, approved=False)
    assert denied["status"] == "approval_required"


def test_e1_proposal_only_no_execution(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "package.json").write_text('{"name":"x"}\n')
    preflight = run_engineering_preflight(
        user_request="Prepare migration patch for Next.js 16 compatibility",
        repo=repo,
    )
    assert preflight["risk_tier"] == EngineeringRiskTier.E1_PROPOSAL.value
    assert execution_allowed(EngineeringRiskTier(preflight["risk_tier"])) is False


def test_engineering_memory_records_outcome(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    preflight = run_engineering_preflight(user_request="Fix workflow rerun", repo=repo)
    from aethos_core.engineering.engineering_memory import record_engineering_outcome

    record_engineering_outcome(
        preflight_id=preflight["preflight_id"],
        execution_id="exe-test",
        status="engineering_execution_complete",
        validation_status="validated",
        task_kind="workflow_fix",
    )
    snap = engineering_memory_snapshot()
    assert snap["total_events"] >= 1


def test_patch_proposal_includes_diff_intelligence(tmp_path: Path):
    repo = _workflow_repo(tmp_path)
    task = intake_engineering_task("Fix workflow rerun", repo=repo)
    proposal = generate_patch_proposal(repo, user_request="fix workflow rerun", task=task)
    assert proposal.get("diff_intelligence")
    assert proposal["diff_intelligence"].get("severity")
