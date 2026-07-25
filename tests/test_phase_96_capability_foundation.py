# SPDX-License-Identifier: Apache-2.0
"""Phase 9.6 capability foundation — governance + readonly surfaces."""

from __future__ import annotations

from aethos_core.agents.coordinator import simulate_task_graph
from aethos_core.channels.registry import channel_registry_dict, format_channel_summary
from aethos_core.chat.capability_foundation_prompts import capability_foundation_reply
from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.chat.operation_preflight_prompts import create_operation_preflight_job_reply
from aethos_core.companion.time_awareness import suggest_for_context
from aethos_core.local_repo.inventory import git_status_readonly, resolve_repo_root
from aethos_core.operations.mutations.execution import run_mutation_execution_dry_run
from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.operations.mutations.taxonomy import CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.job_types import uses_mutation_execution, uses_mutation_preflight
from aethos_core.runtime.jobs import job_store
from aethos_core.social.drafts import draft_social_post


def test_mutation_preflight_job_type_helpers():
    assert uses_mutation_preflight("mutation_preflight") is True
    assert uses_mutation_preflight("operation_preflight") is False
    assert uses_mutation_execution("mutation_execution") is True


def test_mutating_restart_routes_to_mutation_preflight_not_operation_preflight():
    assert create_operation_preflight_job_reply("restart speakglobal-ai on Railway") is None
    out = create_mutation_preflight_job_reply("restart speakglobal-ai on Railway", session_id="pf96")
    assert out is not None
    body, intent, meta = out
    assert intent == "mutation_preflight_job_created"
    assert meta["proposed_job_type"] == CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE
    assert meta["operation_type"] == "restart"
    assert meta["provider"] == "railway"
    assert "no mutation performed" in body.lower()


def test_mutation_preflight_executor_blocks_execution():
    job = authority.create_job(
        title="Railway restart mutation preflight",
        job_type="mutation_preflight",
        params={
            "user_request": "restart speakglobal-ai on Railway",
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
        },
        source="test",
        session_id="mut-pf",
        auto_run=False,
    )
    job_executor.drain_queue_for_tests()
    job_executor.enqueue(job.id)
    assert job_executor.drain_once_for_tests()

    stored = job_store.get(job.id)
    assert stored is not None
    assert stored.status.value == "completed"
    assert stored.params.get("execution_blocked") is True
    assert stored.params.get("mutation_execution_enabled") is False
    assert "mutation execution **not enabled**" in (stored.full_result or "").lower()


def test_mutation_preflight_dry_run_outcome():
    outcome = run_mutation_preflight(
        job_type="mutation_preflight",
        params={
            "user_request": "restart speakglobal-ai on Railway",
            "provider": "railway",
            "operation_type": "restart",
            "target_name": "speakglobal-ai",
        },
    )
    assert outcome.mutation_execution_enabled is False
    assert outcome.preflight_status in ("design_only_blocked", "blocked", "needs_credential")
    assert "Rollback plan" in outcome.full_result
    assert outcome.audit.get("risk_tier")


def test_mutation_execution_dry_run_never_mutates():
    outcome = run_mutation_execution_dry_run(
        params={"provider": "railway", "operation_type": "restart", "target_name": "speakglobal-ai"}
    )
    assert outcome.dry_run is True
    assert outcome.artifact["executed"] is False
    assert outcome.artifact["mutating"] is False


def test_channel_registry_lists_active_and_stubs():
    summary = format_channel_summary()
    assert "Web / Mission Control" in summary
    assert "Telegram" in summary
    assert "`active`" in summary
    assert "Email" in summary
    assert "`stub`" in summary
    names = {c["name"] for c in channel_registry_dict()["channels"]}
    assert "web" in names and "slack" in names


def test_time_aware_suggestions_are_optional():
    for s in suggest_for_context():
        assert s.optional is True
        assert s.blocking is False


def test_social_draft_requires_approval_and_does_not_publish():
    draft = draft_social_post(platform="linkedin", topic="AethOS 9.3M passing")
    payload = draft.to_dict()
    assert payload["approval_required"] is True
    assert payload["execution_enabled"] is False
    assert payload["published"] is False

    out = capability_foundation_reply("draft a LinkedIn post about AethOS 9.3M passing")
    assert out is not None
    body, intent, meta = out
    assert intent == "social_draft"
    assert meta["published"] is False
    assert "not published" in body.lower()


def test_local_repo_readonly_only():
    root = resolve_repo_root("AethOS")
    assert root is not None
    payload = git_status_readonly(root)
    assert payload["read_only"] is True
    assert payload["mutating"] is False

    out = capability_foundation_reply("show supported channels")
    assert out is not None

    from aethos_core.chat.engineering_intelligence import execute_engineering_intent

    eng = execute_engineering_intent("show local repo status for AethOS")
    assert eng is not None
    body, intent, meta = eng
    assert intent == "git_status_snapshot"
    assert meta["read_only"] == "true"
    assert "Writes blocked" in body or "Local git intelligence" in body


def test_screenshot_evidence_does_not_imply_action():
    out = capability_foundation_reply("capture screenshot evidence for Mission Control")
    assert out is not None
    body, intent, meta = out
    assert intent == "screenshot_evidence"
    assert meta["mutating"] is False
    assert "no hidden browser" in body.lower()


def test_multi_agent_coordinator_cannot_self_authorize_mutation():
    graph = simulate_task_graph("ship feature safely")
    payload = graph.to_dict()
    assert payload["execution_enabled"] is False
    assert payload["dry_run"] is True
    assert any("mutation" in c.lower() for c in payload["verification_criteria"])
