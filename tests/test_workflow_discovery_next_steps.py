# SPDX-License-Identifier: Apache-2.0
"""Workflow discovery next-step and proposal tests."""

from __future__ import annotations

from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
    compose_rerun_no_execution_followup,
)
from aethos_core.providers.github.workflow_discovery.workflow_next_steps import (
    compose_generic_ci_workflow_yaml,
    compose_workflow_discovery_next_steps,
    compose_workflow_proposal_reply,
    should_offer_workflow_proposal,
    suggest_starter_workflow_type,
)
from aethos_core.runtime.authority import authority


def setup_function() -> None:
    clear_github_context_for_tests()
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        clear_runtime_context_for_tests,
    )

    clear_runtime_context_for_tests()


def _discovery_no_files(*, actions_status: str = "enabled") -> dict:
    return {
        "repository": "pilotmain/aethos",
        "workflows_dir_found": False,
        "workflow_file_names": [],
        "trigger_analysis": {"all_triggers": []},
        "actions_status": actions_status,
        "default_branch": "main",
        "auth_state": "validated",
        "likely_reason": "No `.github/workflows/` directory exists on the inspected branch.",
        "next_steps": ["Add a workflow under `.github/workflows/`."],
    }


def _seed_noop_preflight(session_id: str, *, workflow_discovery: dict) -> None:
    authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "session_id": session_id,
            "target_name": "pilotmain/aethos",
            "preflight_status": "needs_workflow_resolution",
            "discovery_failure_reason": "no_workflow_runs",
            "workflow_discovery": workflow_discovery,
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )


def test_no_workflow_files_next_steps_include_ci_yml() -> None:
    body = compose_workflow_discovery_next_steps(_discovery_no_files())
    assert "no workflow files exist yet" in body
    assert "`.github/workflows/ci.yml`" in body
    assert "1. Create `.github/workflows/ci.yml`" in body
    assert "Push a commit to generate the first workflow run" in body
    assert "starter workflow proposal" in body.lower()


def test_should_offer_workflow_proposal_when_missing_directory() -> None:
    assert should_offer_workflow_proposal(_discovery_no_files()) is True
    assert should_offer_workflow_proposal({"workflows_dir_found": True, "workflow_file_names": ["ci.yml"]}) is False


def test_suggest_starter_workflow_type_is_generic() -> None:
    starter = suggest_starter_workflow_type(repo_context={"repo_full_name": "pilotmain/aethos"})
    assert starter["type"] == "generic_ci"
    assert starter["filename"] == "ci.yml"


def test_generic_ci_yaml_uses_node_scaffold() -> None:
    yaml_body = compose_generic_ci_workflow_yaml(default_branch="main")
    assert "uses: actions/checkout@v4" in yaml_body
    assert "workflow_dispatch" in yaml_body
    assert "validate:" in yaml_body
    assert "Placeholder validation" in yaml_body


def test_what_should_i_do_next_routes_to_next_step_composer() -> None:
    _seed_noop_preflight("next-steps-route", workflow_discovery=_discovery_no_files())
    reply = compose_rerun_no_execution_followup("what should I do next?", session_id="next-steps-route")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_discovery_next_steps"
    assert "Next best step:" in body
    assert "I checked workflow discovery:" not in body
    assert meta.get("proposal_only") == "false"


def test_draft_workflow_proposal_returns_yaml_proposal() -> None:
    _seed_noop_preflight("proposal-route", workflow_discovery=_discovery_no_files())
    reply = compose_rerun_no_execution_followup("draft workflow proposal", session_id="proposal-route")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_discovery_proposal"
    assert "proposal only" in body.lower()
    assert "```yaml" in body
    assert "name: CI" in body
    assert "no file has been created" in body.lower()
    assert meta.get("proposal_only") == "true"


def test_proposal_reply_standalone() -> None:
    body = compose_workflow_proposal_reply(_discovery_no_files())
    assert "proposal only" in body.lower()
    assert "no commit" in body.lower()
    assert "no push" in body.lower()
    assert "no pr" in body.lower()


def test_proposal_does_not_create_mutation_preflight() -> None:
    from aethos_core.runtime.jobs import job_store

    _seed_noop_preflight("no-preflight-on-proposal", workflow_discovery=_discovery_no_files())
    before = len(job_store.list_all())
    reply = compose_rerun_no_execution_followup("create a CI workflow proposal", session_id="no-preflight-on-proposal")
    assert reply is not None
    after = len(job_store.list_all())
    assert after == before
    assert all(job.job_type != "mutation_execution" for job in job_store.list_all())
