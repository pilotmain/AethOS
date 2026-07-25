# SPDX-License-Identifier: Apache-2.0
"""No-execution route workflow discovery delegation tests."""

from __future__ import annotations

from aethos_core.chat.deterministic import match_project_template, try_partial_template
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
    compose_rerun_no_execution_followup,
    find_latest_rerun_preflight_noop,
)
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
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
        "trigger_analysis": {"all_triggers": []},
        "actions_status": "enabled",
        "default_branch": "main",
        "auth_state": "validated",
        "likely_reason": "No `.github/workflows/` directory exists on the inspected branch.",
        "next_steps": ["Add a workflow under `.github/workflows/`."],
    }


def _seed_noop_preflight(
    session_id: str,
    *,
    job_session_id: str = "default",
    workflow_discovery: dict | None = None,
) -> str:
    params = {
        "provider": "github",
        "operation_type": "workflow_rerun",
        "session_id": session_id,
        "target_name": "pilotmain/aethos",
        "preflight_status": "needs_workflow_resolution",
        "discovery_failure_reason": "no_workflow_runs",
        "workflow_discovery": workflow_discovery or _discovery_no_files(),
    }
    job = authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params=params,
        source="test",
        session_id=job_session_id,
        auto_run=False,
    )
    return job.id


def test_no_execution_what_should_i_do_next_delegates_to_workflow_next_steps() -> None:
    session_id = "noop-next-steps"
    _seed_noop_preflight(session_id, workflow_discovery=_discovery_no_files())
    reply = compose_rerun_no_execution_followup("what should I do next?", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_discovery_next_steps"
    assert meta.get("route_id") == "github_rerun_no_execution"
    assert meta.get("workflow_discovery_delegated") == "true"
    assert "no workflow files exist yet" in body
    assert "`.github/workflows/ci.yml`" in body


def test_no_execution_draft_workflow_proposal_delegates_to_yaml_proposal() -> None:
    session_id = "noop-proposal"
    _seed_noop_preflight(session_id, workflow_discovery=_discovery_no_files())
    reply = compose_rerun_no_execution_followup("draft workflow proposal", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_discovery_proposal"
    assert meta.get("route_id") == "github_rerun_no_execution"
    assert meta.get("delegated_handler") == "workflow_discovery_proposal"
    assert "```yaml" in body
    assert "name: CI" in body
    assert "proposal only" in body.lower()


def test_no_execution_delegates_when_job_session_id_differs_but_params_match() -> None:
    session_id = "tg-live-session"
    _seed_noop_preflight(session_id, job_session_id="default", workflow_discovery=_discovery_no_files())
    state = find_latest_rerun_preflight_noop(session_id=session_id)
    assert state is not None
    assert state.get("workflow_discovery") is not None

    reply = compose_rerun_no_execution_followup("what next?", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_discovery_next_steps"
    assert meta.get("route_id") == "github_rerun_no_execution"


def test_no_execution_create_ci_workflow_delegates_to_proposal() -> None:
    session_id = "noop-create-ci"
    _seed_noop_preflight(session_id, workflow_discovery=_discovery_no_files())
    reply = compose_rerun_no_execution_followup("create ci workflow", session_id=session_id)
    assert reply is not None
    _body, intent, meta = reply
    assert intent == "workflow_discovery_proposal"
    assert meta.get("proposal_only") == "true"


def test_mission_control_template_suppressed_when_no_execution_delegates() -> None:
    session_id = "noop-template-block"
    _seed_noop_preflight(session_id, workflow_discovery=_discovery_no_files())
    assert match_project_template("what should I do next?", session_id=session_id) is None
    assert try_partial_template("what should I do next?", session_id=session_id) is None


def test_resolve_chat_turn_uses_no_execution_delegation() -> None:
    session_id = "noop-chat-turn"
    _seed_noop_preflight(session_id, workflow_discovery=_discovery_no_files())
    result = resolve_chat_turn("what should I do next?", session_id=session_id, apply_relational_layer=False)
    assert result.intent == "workflow_discovery_next_steps"
    assert result.meta.get("route_id") in {"github_rerun_no_execution", "workflow_discovery_next_steps"}
    assert "Mission Control" not in result.reply


def test_proposal_does_not_create_mutation_preflight() -> None:
    session_id = "noop-no-mutation"
    _seed_noop_preflight(session_id, workflow_discovery=_discovery_no_files())
    before = len(job_store.list_all())
    reply = compose_rerun_no_execution_followup("draft workflow proposal", session_id=session_id)
    assert reply is not None
    assert len(job_store.list_all()) == before


def test_proposal_forced_when_discovery_missing_from_state() -> None:
    """Fix 78: delegation must never return None when proposal intent matches."""
    session_id = "noop-forced"
    params = {
        "provider": "github",
        "operation_type": "workflow_rerun",
        "session_id": session_id,
        "target_name": "pilotmain/aethos",
        "preflight_status": "needs_workflow_resolution",
        "discovery_failure_reason": "no_workflow_runs",
    }
    authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params=params,
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
        _try_workflow_discovery_delegation,
    )

    state = find_latest_rerun_preflight_noop(session_id=session_id)
    assert state is not None
    assert state.get("workflow_discovery") is None

    result = _try_workflow_discovery_delegation("draft workflow proposal", session_id=session_id, state=state)
    assert result is not None, "delegation must not return None on proposal intent"
    body, intent, meta = result
    assert intent == "workflow_discovery_proposal"
    assert meta.get("workflow_discovery_delegated") == "true"
    assert meta.get("workflow_discovery_proposal_forced") in ("true", "false")
    assert meta.get("blocked_handlers") == "llm_fallback,project_template,generic_workflow_planner"
    assert "name: CI" in body
    assert "proposal only" in body.lower()


def test_all_required_proposal_phrases_match() -> None:
    """Fix 78: all required proposal phrases must be recognized."""
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        is_hard_workflow_discovery_proposal_intent,
    )
    from aethos_core.providers.github.workflow_discovery.workflow_next_steps import (
        is_workflow_proposal_intent as soft_proposal,
    )

    required = [
        "draft workflow proposal",
        "create ci workflow",
        "create ci proposal",
        "propose github actions workflow",
        "draft ci.yml",
        "generate ci workflow",
    ]
    for phrase in required:
        assert is_hard_workflow_discovery_proposal_intent(phrase) or soft_proposal(phrase), (
            f"phrase not matched: {phrase!r}"
        )


def test_proposal_trace_includes_all_required_fields() -> None:
    """Fix 78: route trace must contain forced delegation metadata."""
    session_id = "noop-trace-fields"
    _seed_noop_preflight(session_id, workflow_discovery=_discovery_no_files())
    reply = compose_rerun_no_execution_followup("draft workflow proposal", session_id=session_id)
    assert reply is not None
    _body, _intent, meta = reply
    assert meta.get("workflow_discovery_delegated") == "true"
    assert meta.get("delegated_handler") == "workflow_discovery_proposal"
    assert "workflow_discovery_proposal_forced" in meta
    assert "llm_fallback" in meta.get("blocked_handlers", "")
    assert "project_template" in meta.get("blocked_handlers", "")
    assert "generic_workflow_planner" in meta.get("blocked_handlers", "")
