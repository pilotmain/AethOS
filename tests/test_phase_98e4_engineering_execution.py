# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8E.4 — Governed engineering execution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from aethos_core.chat.engineering_intelligence import classify_engineering_intent, execute_engineering_intent
from aethos_core.engineering.governance.engineering_execution import run_engineering_execution
from aethos_core.engineering.governance.engineering_preflight import run_engineering_preflight
from aethos_core.engineering.governance.engineering_scope import EngineeringRiskTier, classify_engineering_risk, execution_allowed
from aethos_core.engineering.patch_engine import generate_patch_proposal
from aethos_core.engineering.pr_generation import generate_pr_draft
from aethos_core.engineering.task_intake import intake_engineering_task
from aethos_core.local_workspace.mutation_workspace import create_mutation_workspace, list_mutation_workspaces
from aethos_core.operations.reality_loop import run_reality_loop_scan


def test_task_intake_workflow_fix():
    task = intake_engineering_task("Fix the GitHub workflow rerun failure in AethOS")
    assert task["kind"] == "workflow_fix"
    assert task.get("affected_files")
    assert task.get("risk_tier")


def test_engineering_preflight_no_execution(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "aethos_core").mkdir(parents=True)
    path = repo / "aethos_core/providers/github/shared/workflow_resolution.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# stub\n")
    preflight = run_engineering_preflight(
        user_request="Fix the GitHub workflow failure in AethOS",
        repo=repo,
    )
    assert preflight.get("approval_status") == "pending"
    assert preflight.get("execution_enabled") is False
    assert preflight.get("patch_proposal")
    assert "approval required" in (preflight.get("report") or "").lower()


def test_patch_proposal_scoped(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    path = repo / "aethos_core/providers/github/shared/workflow_resolution.py"
    path.parent.mkdir(parents=True)
    path.write_text("x = 1\n")
    proposal = generate_patch_proposal(repo, user_request="fix workflow rerun", task=intake_engineering_task("fix workflow"))
    assert proposal.get("files_affected")
    assert proposal.get("unified_diffs") is not None
    assert proposal.get("approval_status") == "pending"
    assert proposal.get("execution_enabled") is False


def test_execution_requires_approval(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    preflight = {"risk_tier": EngineeringRiskTier.E2_BRANCH_DIFF.value, "patch_proposal": {"files_affected": []}}
    denied = run_engineering_execution(preflight=preflight, repo=repo, approved=False)
    assert denied.get("status") == "approval_required"


def test_mutation_workspace_isolated(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("original\n")
    ws = create_mutation_workspace(repo_path=repo, file_scope=["README.md"])
    assert ws.get("sandbox_path")
    assert Path(ws["sandbox_path"]).is_dir()
    assert (Path(ws["sandbox_path"]) / "README.md").read_text() == "original\n"


def test_engineering_risk_tiers():
    assert classify_engineering_risk(operation="engineering_preflight") == EngineeringRiskTier.E1_PROPOSAL
    assert execution_allowed(EngineeringRiskTier.E2_BRANCH_DIFF) is True
    assert execution_allowed(EngineeringRiskTier.E5_BLOCKED) is False


def test_pr_draft_no_merge():
    draft = generate_pr_draft(
        preflight={"task": {"title": "Fix workflow"}, "patch_proposal": {"patch_summary": "scoped fix", "risk_areas": ["LOW"]}, "risk_tier": "E2_branch_diff"},
        execution={"validation": {"validation_status": "validated", "pass_count": 3, "fail_count": 0}},
    )
    assert draft.get("merge_enabled") is False
    assert draft.get("auto_merge") is False
    assert "Fix workflow" in draft.get("body", "")


def test_reality_loop_readonly():
    scan = run_reality_loop_scan()
    assert scan.get("readonly") is True
    assert scan.get("background_mutations") is False


def test_engineering_intent_classification():
    intent = classify_engineering_intent("Fix the GitHub workflow failure in AethOS")
    assert intent is not None
    assert intent.intent.value == "engineering_preflight"


def test_engineering_preflight_chat_lane(tmp_path: Path):
    with patch("aethos_core.local_workspace.readonly.actions._repo_from_hint", return_value=tmp_path):
        tmp_path.mkdir(exist_ok=True)
        (tmp_path / "aethos_core").mkdir(exist_ok=True)
        result = execute_engineering_intent("Fix the GitHub workflow failure in AethOS")
    assert result is not None
    body, status, meta = result
    assert status == "engineering_preflight"
    assert meta.get("approval_status") == "pending"
