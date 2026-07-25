# SPDX-License-Identifier: Apache-2.0
"""GitHub rerun no-execution follow-up tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.mutation_execution_chat import compose_mutation_execution_truth_reply
from aethos_core.operation_lifecycle.lifecycle_followup_router import compose_lifecycle_followup_reply
from aethos_core.providers.github.context.github_context_store import (
    clear_github_context_for_tests,
    save_github_context_from_evidence,
)
from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
    compose_rerun_no_execution_followup,
    find_latest_rerun_preflight_noop,
    is_rerun_no_execution_state,
)
from aethos_core.runtime.authority import authority


def setup_function() -> None:
    clear_github_context_for_tests()


def _seed_repo(session_id: str) -> None:
    save_github_context_from_evidence(
        session_id,
        {
            "repository": "pilotmain/aethos",
            "repo": {"full_name": "pilotmain/aethos", "default_branch": "main"},
            "branch": {"branch": "main", "sha": "abc123"},
            "commits": {"commits": [{"sha": "abc123", "message": "fix", "author": "raya"}]},
            "checks": {"ok": True, "failed_count": 0, "checks": []},
            "workflow_runs": {"ok": True, "runs": []},
            "workflow_diagnostic": {"ok": True, "latest_failed_run": None},
        },
    )


def _create_noop_preflight(
    session_id: str,
    *,
    discovery_reason: str = "no_workflow_runs",
    workflow_discovery: dict | None = None,
) -> str:
    params = {
        "user_request": "rerun the failed GitHub workflow",
        "provider": "github",
        "operation_type": "workflow_rerun",
        "session_id": session_id,
        "target_name": "pilotmain/aethos",
        "preflight_status": "needs_workflow_resolution",
        "discovery_failure_reason": discovery_reason,
        "summary": (
            f"Mutation preflight (T2): discovery failed ({discovery_reason.replace('_', ' ')}). "
            "No workflow rerun performed."
        ),
        "ui_action_available": False,
        "approval_required": False,
    }
    if workflow_discovery:
        params["workflow_discovery"] = workflow_discovery
    job = authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params=params,
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    return job.id


def test_find_latest_noop_preflight() -> None:
    _seed_repo("noop-find")
    job_id = _create_noop_preflight("noop-find")
    state = find_latest_rerun_preflight_noop(session_id="noop-find")
    assert state is not None
    assert state["preflight_job_id"] == job_id
    assert state["repository"] == "pilotmain/aethos"
    assert is_rerun_no_execution_state(session_id="noop-find") is True


def test_what_happened_after_approval_no_execution() -> None:
    _seed_repo("noop-after")
    _create_noop_preflight("noop-after")
    reply = compose_rerun_no_execution_followup("what happened after approval?", session_id="noop-after")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "github_workflow_rerun_no_execution_followup"
    assert "no approval/execution step" in body
    assert "pilotmain/aethos" in body
    assert "no rerun performed" in body
    assert "no downstream deployment expected" in body
    assert "execution job" not in body.lower()
    assert meta.get("rerun_executed") == "false"


def test_deployment_reach_runtime_no_execution() -> None:
    _seed_repo("noop-deploy")
    _create_noop_preflight("noop-deploy")
    reply = compose_rerun_no_execution_followup("did deployment reach runtime?", session_id="noop-deploy")
    assert reply is not None
    body, _, _ = reply
    assert "No deployment was expected" in body
    assert "pilotmain/aethos" in body
    assert "not triggered" in body.lower()


def test_failure_boundary_no_execution() -> None:
    _seed_repo("noop-boundary")
    _create_noop_preflight(
        "noop-boundary",
        workflow_discovery={
            "repository": "pilotmain/aethos",
            "workflows_dir_found": False,
            "workflow_file_names": [],
            "trigger_analysis": {"all_triggers": []},
            "actions_status": "unknown",
            "default_branch": "main",
            "likely_reason": "No `.github/workflows/` directory exists on the inspected branch — GitHub Actions workflows are not configured.",
            "next_steps": ["Add a workflow under `.github/workflows/`."],
        },
    )
    reply = compose_rerun_no_execution_followup("where is the failure boundary now?", session_id="noop-boundary")
    assert reply is not None
    body, _, _ = reply
    assert "no new failure boundary from a rerun" in body
    assert "GitHub: no workflow files configured" in body
    assert "Vercel/Railway: not triggered" in body


def test_lifecycle_followup_prefers_no_execution_truth() -> None:
    _seed_repo("noop-lifecycle")
    _create_noop_preflight("noop-lifecycle")
    reply = compose_lifecycle_followup_reply("what happened after approval?", session_id="noop-lifecycle")
    assert reply is not None
    body, intent, _ = reply
    assert intent == "github_workflow_rerun_no_execution_followup"
    assert "no approval/execution step" in body


def test_mutation_execution_truth_suppresses_missing_job_message() -> None:
    _seed_repo("noop-exec-truth")
    _create_noop_preflight("noop-exec-truth")
    reply = compose_mutation_execution_truth_reply("what happened after approval?", session_id="noop-exec-truth")
    assert reply is not None
    body, intent, _ = reply
    assert intent == "github_workflow_rerun_no_execution_followup"
    assert "couldn't find a governed mutation execution job" not in body


@patch("aethos_core.operations.mutations.preflight._mutation_provider_auth_block", return_value=None)
def test_no_workflow_runs_preflight_end_to_end(_auth, monkeypatch) -> None:
    from aethos_core.config import get_settings
    from aethos_core.providers.github.context.github_context_store import save_github_rerun_context

    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    _seed_repo("noop-e2e")
    job_id = _create_noop_preflight(
        "noop-e2e",
        discovery_reason="no_workflow_runs",
        workflow_discovery={
            "repository": "pilotmain/aethos",
            "workflows_dir_found": False,
            "workflow_file_names": [],
            "trigger_analysis": {"all_triggers": []},
            "actions_status": "unknown",
            "default_branch": "main",
            "likely_reason": "No `.github/workflows/` directory exists on the inspected branch — GitHub Actions workflows are not configured.",
            "next_steps": ["Add a workflow under `.github/workflows/`."],
        },
    )
    save_github_rerun_context(
        "noop-e2e",
        {
            "rerun_target_repo": "pilotmain/aethos",
            "preflight_job_id": job_id,
            "verification_status": "needs_workflow_resolution",
            "discovery_failure_reason": "no_workflow_runs",
        },
    )
    reply = compose_rerun_no_execution_followup("what happened after approval?", session_id="noop-e2e")
    assert reply is not None
    body, _, _ = reply
    assert "no approval/execution step" in body
    assert "workflow discovery" in body.lower()
