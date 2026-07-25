# SPDX-License-Identifier: Apache-2.0
"""Fix 81 — Workflow creation context binding tests."""

from __future__ import annotations

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
    compose_rerun_no_execution_followup,
)
from aethos_core.providers.github.workflow_creation.workflow_creation_context import (
    clear_for_tests as clear_creation_ctx,
    get_pending_workflow_proposal,
    has_pending_workflow_proposal,
)
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


def setup_function() -> None:
    clear_github_context_for_tests()
    clear_runtime_context_for_tests()
    clear_creation_ctx()
    job_store.clear_for_tests()


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
            "workflow_discovery": {
                "repository": "pilotmain/aethos",
                "workflows_dir_found": False,
                "workflow_file_names": [],
                "workflow_files": [],
                "actions_status": "enabled",
                "default_branch": "main",
                "likely_reason": "No workflows dir.",
            },
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    return job.id


def test_proposal_persists_creation_context() -> None:
    session_id = "ctx-persist"
    _seed_noop_preflight(session_id)
    assert not has_pending_workflow_proposal(session_id=session_id)

    compose_rerun_no_execution_followup("draft workflow proposal", session_id=session_id)

    ctx = get_pending_workflow_proposal(session_id=session_id)
    assert ctx is not None
    assert ctx["repo"] == "pilotmain/aethos"
    assert ctx["file_path"] == ".github/workflows/ci.yml"
    assert ctx["branch"] == "add-ci-workflow"
    assert ctx["base_branch"] == "main"
    assert "name: CI" in ctx["proposal_yaml"]


def test_create_this_workflow_file_uses_context() -> None:
    session_id = "ctx-create"
    _seed_noop_preflight(session_id)
    compose_rerun_no_execution_followup("draft workflow proposal", session_id=session_id)

    job_store.clear_for_tests()
    clear_runtime_context_for_tests()

    result = resolve_chat_turn("create this workflow file", session_id=session_id, apply_relational_layer=False)
    assert result.intent == "workflow_creation_governed_plan"
    assert result.meta.get("route_id") in ("github_workflow_lane", "workflow_creation_plan")
    assert "governed workflow-file creation plan" in result.reply
    assert "add-ci-workflow" in result.reply


def test_push_to_main_blocked() -> None:
    session_id = "ctx-blocked"
    _seed_noop_preflight(session_id)
    compose_rerun_no_execution_followup("draft workflow proposal", session_id=session_id)

    job_store.clear_for_tests()
    clear_runtime_context_for_tests()

    result = resolve_chat_turn("push the workflow to main", session_id=session_id, apply_relational_layer=False)
    assert result.intent == "workflow_creation_governed_plan"
    assert "will not" in result.reply
    assert "T3" in result.reply
    assert "blocked" in result.reply.lower()


def test_cancel_clears_context() -> None:
    session_id = "ctx-cancel"
    _seed_noop_preflight(session_id)
    compose_rerun_no_execution_followup("draft workflow proposal", session_id=session_id)
    assert has_pending_workflow_proposal(session_id=session_id)

    result = resolve_chat_turn("cancel", session_id=session_id, apply_relational_layer=False)
    assert result.intent == "workflow_creation_cancelled"
    assert "Cancelled" in result.reply
    assert "No file, branch, commit" in result.reply


def test_no_branch_file_commit_pr_created() -> None:
    session_id = "ctx-no-side-effects"
    _seed_noop_preflight(session_id)
    before = len(job_store.list_all())
    compose_rerun_no_execution_followup("draft workflow proposal", session_id=session_id)

    job_store.clear_for_tests()
    clear_runtime_context_for_tests()

    resolve_chat_turn("create this workflow file", session_id=session_id, apply_relational_layer=False)
    after_create_jobs = [
        j for j in job_store.list_all()
        if j.job_type in ("mutation_execution", "branch_creation", "file_creation", "pr_creation")
    ]
    assert len(after_create_jobs) == 0, "No execution jobs should be created at plan stage"
