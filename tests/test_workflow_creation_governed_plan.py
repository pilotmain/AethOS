# SPDX-License-Identifier: Apache-2.0
"""Fix 80 — Governed workflow file creation plan tests."""

from __future__ import annotations

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
    compose_rerun_no_execution_followup,
)
from aethos_core.providers.github.workflow_discovery.workflow_creation_plan import (
    classify_workflow_creation_risk,
    compose_governed_workflow_creation_plan,
    is_direct_main_write_requested,
    is_workflow_creation_intent,
)
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
from aethos_core.operations.mutations.risk import MutationRiskTier
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


def setup_function() -> None:
    clear_github_context_for_tests()
    clear_runtime_context_for_tests()
    job_store.clear_for_tests()


def _discovery_no_files() -> dict:
    return {
        "repository": "pilotmain/aethos",
        "workflows_dir_found": False,
        "workflow_file_names": [],
        "workflow_files": [],
        "actions_status": "enabled",
        "default_branch": "main",
        "likely_reason": "No `.github/workflows/` directory exists.",
    }


def _seed_noop_preflight(session_id: str) -> str:
    job = authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "session_id": session_id,
            "target_name": "pilotmain/aethos",
            "preflight_status": "needs_workflow_resolution",
            "discovery_failure_reason": "no_workflow_runs",
            "workflow_discovery": _discovery_no_files(),
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    return job.id


def test_create_workflow_file_produces_governed_plan() -> None:
    session_id = "gov-create"
    _seed_noop_preflight(session_id)
    reply = compose_rerun_no_execution_followup("create the workflow file", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_creation_governed_plan"
    assert meta.get("governed_plan") == "true"
    assert meta.get("workflow_discovery_delegated") == "true"
    assert "governed workflow-file creation plan" in body
    assert "add-ci-workflow" in body
    assert ".github/workflows/ci.yml" in body
    assert "approval" in body.lower()


def test_governed_plan_does_not_execute_directly() -> None:
    session_id = "gov-no-exec"
    _seed_noop_preflight(session_id)
    before = len(job_store.list_all())
    reply = compose_rerun_no_execution_followup("create the workflow file", session_id=session_id)
    assert reply is not None
    after = len(job_store.list_all())
    assert after == before, "No new jobs should be created — plan only"


def test_governed_plan_proposes_branch_strategy() -> None:
    session_id = "gov-branch"
    _seed_noop_preflight(session_id)
    reply = compose_rerun_no_execution_followup("create the workflow file", session_id=session_id)
    assert reply is not None
    body, _intent, _meta = reply
    assert "add-ci-workflow" in body
    assert "Create branch" in body
    assert "Open PR" in body


def test_governed_plan_proposes_pr_strategy() -> None:
    session_id = "gov-pr"
    _seed_noop_preflight(session_id)
    reply = compose_rerun_no_execution_followup("create the workflow file", session_id=session_id)
    assert reply is not None
    body, _intent, _meta = reply
    assert "Open PR" in body
    assert "main" in body


def test_governed_plan_requires_approval() -> None:
    session_id = "gov-approval"
    _seed_noop_preflight(session_id)
    reply = compose_rerun_no_execution_followup("create the workflow file", session_id=session_id)
    assert reply is not None
    body, _intent, _meta = reply
    assert "requires approval" in body
    assert "approve" in body.lower()
    assert "No file has been created yet" in body


def test_direct_main_write_blocked() -> None:
    session_id = "gov-blocked"
    _seed_noop_preflight(session_id)
    reply = compose_rerun_no_execution_followup("push the workflow to main", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_creation_governed_plan"
    assert "will not" in body
    assert "T3" in body
    assert "blocked" in body.lower()


def test_risk_tier_t2_for_branch_pr() -> None:
    assert classify_workflow_creation_risk("create the workflow file") == MutationRiskTier.T2_LOW_RISK


def test_risk_tier_t3_for_direct_main() -> None:
    assert classify_workflow_creation_risk("push to main") == MutationRiskTier.T3_PRODUCTION


def test_intent_detection_coverage() -> None:
    positives = [
        "create the workflow file",
        "add the workflow file",
        "write the ci.yml",
        "create ci.yml",
        "implement the workflow",
        "set up the workflow",
        "make the workflow file",
    ]
    for phrase in positives:
        assert is_workflow_creation_intent(phrase), f"not detected: {phrase!r}"

    negatives = [
        "draft workflow proposal",
        "what should I do next?",
        "show route trace",
    ]
    for phrase in negatives:
        assert not is_workflow_creation_intent(phrase), f"false positive: {phrase!r}"


def test_direct_main_detection() -> None:
    assert is_direct_main_write_requested("push to main")
    assert is_direct_main_write_requested("push the workflow to main")
    assert is_direct_main_write_requested("commit to main")
    assert not is_direct_main_write_requested("create the workflow file")


def test_resolve_chat_turn_governed_plan() -> None:
    session_id = "gov-turn"
    _seed_noop_preflight(session_id)
    result = resolve_chat_turn("create the workflow file", session_id=session_id, apply_relational_layer=False)
    assert result.intent == "workflow_creation_governed_plan"
    assert "governed workflow-file creation plan" in result.reply
    assert result.meta.get("route_id") in ("github_workflow_lane", "workflow_creation_plan")
    assert result.meta.get("governed_plan") == "true" or result.meta.get("workflow_lane_stage") == "creation_plan_ready"


def test_no_mutation_preflight_job_created_at_plan_stage() -> None:
    """Governed plan does NOT create a mutation preflight job — only proposal."""
    session_id = "gov-no-preflight"
    _seed_noop_preflight(session_id)
    before_jobs = [
        j for j in job_store.list_all()
        if j.job_type == "mutation_preflight" and (j.params or {}).get("operation_type") == "create_workflow_file"
    ]
    compose_rerun_no_execution_followup("create this workflow file", session_id=session_id)
    after_jobs = [
        j for j in job_store.list_all()
        if j.job_type == "mutation_preflight" and (j.params or {}).get("operation_type") == "create_workflow_file"
    ]
    assert len(after_jobs) == len(before_jobs), "No new mutation preflight job should be created at plan stage"
