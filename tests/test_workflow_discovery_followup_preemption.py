# SPDX-License-Identifier: Apache-2.0
"""Workflow discovery follow-up preemption tests."""

from __future__ import annotations

from aethos_core.capabilities.capability_executor import execute_cognition_strategy
from aethos_core.chat.deterministic import match_project_template, try_partial_template
from aethos_core.chat.handlers import resolve_handler
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.operational_cognition.types import OperationalCognitionDecision
from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight
from aethos_core.operational_thread_memory.thread_persistence import clear_threads_for_tests
from aethos_core.operational_thread_memory.thread_reply_composer import compose_operational_thread_followup
from aethos_core.provider_topology.followup_lock import compose_thread_continuation_reply
from aethos_core.providers.github.context.github_context_store import (
    clear_github_context_for_tests,
    save_github_rerun_context,
)
from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
    route_workflow_discovery_followup,
)
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
    enforce_workflow_discovery_absolute_lane,
    hydrate_workflow_discovery_context,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from aethos_core.world_model.investigation_strategy_router import compose_investigation_strategy_route_reply


def setup_function() -> None:
    clear_github_context_for_tests()
    clear_threads_for_tests()
    job_store.clear_for_tests()
    clear_runtime_context_for_tests()


def test_hydrates_discovery_from_preflight_job_params_without_rerun_context() -> None:
    session_id = "tg-chat-42-user-9"
    authority.create_job(
        title="GitHub workflow rerun preflight",
        job_type="mutation_preflight",
        params={
            "provider": "github",
            "operation_type": "workflow_rerun",
            "session_id": session_id,
            "target_name": "pilotmain/aethos",
            "preflight_status": "needs_workflow_resolution",
            "workflow_discovery": _discovery_no_files(),
        },
        source="test",
        session_id="default",
        auto_run=False,
    )

    ctx = hydrate_workflow_discovery_context(session_id=session_id)
    assert ctx.hydrated is True
    assert ctx.has_no_workflows is True
    assert ctx.github_repo == "pilotmain/aethos"
    assert ctx.hydration_source.startswith("job_store:")

    result = resolve_chat_turn("what should I do next?", session_id=session_id, apply_relational_layer=False)
    assert result.intent == "workflow_discovery_next_steps"
    assert result.meta.get("workflow_discovery_hydrated") == "true"
    assert "Mission Control" not in result.reply


def _discovery_no_files(*, actions_status: str = "enabled") -> dict:
    return {
        "repository": "pilotmain/aethos",
        "workflows_dir_found": False,
        "workflow_file_names": [],
        "workflow_files": [],
        "trigger_analysis": {"all_triggers": []},
        "actions_status": actions_status,
        "default_branch": "main",
        "auth_state": "validated",
        "likely_reason": "No `.github/workflows/` directory exists on the inspected branch.",
        "next_steps": ["Add a workflow under `.github/workflows/`."],
    }


def _seed_discovery_context(session_id: str, *, workflow_discovery: dict) -> None:
    save_github_rerun_context(
        session_id,
        {
            "rerun_target_repo": "pilotmain/aethos",
            "discovery_failure_reason": "no_workflow_runs",
            "workflow_discovery": workflow_discovery,
        },
    )


def _seed_active_railway_thread(session_id: str) -> None:
    preflight = authority.create_job(
        title="Railway workflow rerun preflight",
        job_type="mutation_preflight",
        params={
            "provider": "railway",
            "operation_type": "workflow_rerun",
            "target_name": "unknown",
            "target": {
                "project_name": "pilotcore-sales-engine",
                "environment": "production",
                "service_name": "unknown",
                "resolved": True,
            },
            "user_request": "rerun railway workflow for unknown",
        },
        source="test",
        session_id=session_id,
        auto_run=False,
    )
    sync_thread_from_preflight(job=preflight, user_request="rerun railway workflow for unknown")


def test_hard_preempt_when_no_workflow_files_context_exists() -> None:
    session_id = "wf-hard-preempt"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())
    hydrate_workflow_discovery_context(session_id=session_id)
    reply = enforce_workflow_discovery_absolute_lane("what should I do next?", session_id=session_id)
    assert reply is not None
    assert enforce_workflow_discovery_absolute_lane("draft workflow proposal", session_id=session_id) is not None


def test_what_should_i_do_next_uses_workflow_discovery_context() -> None:
    session_id = "wf-discovery-next"
    discovery = _discovery_no_files()
    _seed_discovery_context(session_id, workflow_discovery=discovery)
    _seed_active_railway_thread(session_id)

    thread = compose_thread_continuation_reply("what should I do next?", session_id=session_id)
    assert thread is None

    reply = enforce_workflow_discovery_absolute_lane("what should I do next?", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_discovery_next_steps"
    assert "no workflow files exist yet" in body
    assert "1. Create `.github/workflows/ci.yml`" in body
    assert meta.get("workflow_discovery_hydrated") == "true"
    assert meta.get("workflow_discovery_preempted") == "true"
    assert "project_template" in str(meta.get("blocked_handlers") or "")


def test_how_should_i_continue_hard_routes_to_next_steps() -> None:
    session_id = "wf-discovery-continue"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())
    reply = enforce_workflow_discovery_absolute_lane("how should I continue?", session_id=session_id)
    assert reply is not None
    body, intent, _meta = reply
    assert intent == "workflow_discovery_next_steps"
    assert "Push a commit to generate the first workflow run" in body


def test_draft_workflow_proposal_returns_ci_yml_proposal() -> None:
    session_id = "wf-discovery-proposal"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())
    _seed_active_railway_thread(session_id)

    reply = enforce_workflow_discovery_absolute_lane("draft workflow proposal", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_discovery_proposal"
    assert "```yaml" in body
    assert "name: CI" in body
    assert "Placeholder validation" in body
    assert "proposal only" in body.lower()
    assert "no commit" in body.lower()
    assert meta.get("proposal_only") == "true"


def test_active_railway_thread_yields_in_handler_chain() -> None:
    session_id = "wf-discovery-handler"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())
    _seed_active_railway_thread(session_id)

    handled = resolve_handler("what should I do next?", session_id=session_id)
    assert handled is not None
    body, intent, _meta = handled
    assert intent == "workflow_discovery_next_steps"
    assert "continuing the active Railway" not in body
    assert "Phase 2" not in body


def test_generic_workflow_planner_yields() -> None:
    session_id = "wf-discovery-generic"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())

    assert match_project_template("what should I do next?", session_id=session_id) is None
    assert try_partial_template("what should I do next?", session_id=session_id) is None
    assert compose_investigation_strategy_route_reply("what next?", session_id=session_id) is None
    assert compose_investigation_strategy_route_reply("how should we continue?", session_id=session_id) is None
    assert compose_operational_thread_followup("what next?", session_id=session_id) is None


def test_resolve_chat_turn_hard_preempts_mission_control_template() -> None:
    session_id = "wf-discovery-chat-turn"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())
    _seed_active_railway_thread(session_id)

    result = resolve_chat_turn("what should I do next?", session_id=session_id, apply_relational_layer=False)
    assert result.intent == "workflow_discovery_next_steps"
    assert "Mission Control" not in result.reply
    assert "`.github/workflows/ci.yml`" in result.reply


def test_resolve_chat_turn_proposal_without_clarification() -> None:
    session_id = "wf-discovery-chat-proposal"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())

    result = resolve_chat_turn("draft workflow proposal", session_id=session_id, apply_relational_layer=False)
    assert result.intent == "workflow_discovery_proposal"
    assert "```yaml" in result.reply
    assert "no push" in result.reply.lower()


def test_cognition_executor_prefers_workflow_discovery_over_active_thread() -> None:
    session_id = "wf-discovery-cognition"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())
    _seed_active_railway_thread(session_id)

    decision = OperationalCognitionDecision(
        intent="status_check",
        scope="active_target",
        provider="railway",
        target="unknown",
        confidence=0.8,
        reasoning_chain=["test"],
        execution_strategy="active_thread_followup",
        capabilities=[],
        meta={},
    )
    result = execute_cognition_strategy(
        decision,
        "what should I do next?",
        session_id=session_id,
        stop_before="active_thread_followup",
    )
    assert result.handled is True
    assert result.intent in {"workflow_discovery_next_steps", "github_workflow_discovery_next_steps"}
    assert result.route_id in {"workflow_discovery_followup", "github_rerun_no_execution", "workflow_discovery_next_steps"}


def test_workflow_discovery_router_when_no_exec_state_missing() -> None:
    session_id = "wf-discovery-no-noexec"
    save_github_rerun_context(
        session_id,
        {
            "rerun_target_repo": "pilotmain/aethos",
            "workflow_discovery": _discovery_no_files(),
        },
    )
    _seed_active_railway_thread(session_id)

    from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
        compose_rerun_no_execution_followup,
    )

    assert compose_rerun_no_execution_followup("what should I do next?", session_id=session_id) is None

    reply = route_workflow_discovery_followup("what should I do next?", session_id=session_id)
    assert reply is not None
    body, intent, meta = reply
    assert intent == "workflow_discovery_next_steps"
    assert meta.get("matched_module") == "providers.github.workflow_discovery.workflow_discovery_followup_router"
    assert "`.github/workflows/ci.yml`" in body


def test_complete_chat_generative_fallback_yields_to_hydrated_discovery() -> None:
    session_id = "wf-discovery-llm"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())

    from aethos_core.provider.completion import generative_fallback

    result = generative_fallback("draft workflow proposal", session_id=session_id)
    assert result.used_llm is False
    assert "name: CI" in result.text
    assert "Mission Control" not in result.text
    assert "generative intelligence is configured" not in result.text.lower()


def test_proposal_does_not_create_mutation_preflight() -> None:
    session_id = "wf-discovery-no-mutation"
    _seed_discovery_context(session_id, workflow_discovery=_discovery_no_files())
    before = len(job_store.list_all())

    reply = enforce_workflow_discovery_absolute_lane("create ci proposal", session_id=session_id)
    assert reply is not None
    after = len(job_store.list_all())
    assert after == before
    assert all(job.job_type != "mutation_execution" for job in job_store.list_all())
