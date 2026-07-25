# SPDX-License-Identifier: Apache-2.0
"""Fix 82 — GitHub Workflow Lane Hard Router tests."""

from __future__ import annotations

from aethos_core.chat.route_trace import clear_route_traces_for_tests, get_last_route_trace
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.providers.github.context.github_context_store import clear_github_context_for_tests
from aethos_core.providers.github.workflow_creation.workflow_creation_context import clear_for_tests as clear_creation_ctx
from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
    clear_runtime_context_for_tests,
)
from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
    clear_for_tests as clear_lane,
    get_workflow_lane_state,
    is_workflow_lane_intent,
    route_workflow_lane,
)
from aethos_core.runtime.jobs import job_store


def setup_function() -> None:
    clear_github_context_for_tests()
    clear_runtime_context_for_tests()
    clear_route_traces_for_tests()
    clear_creation_ctx()
    clear_lane()
    job_store.clear_for_tests()


# ─── Intent Detection ────────────────────────────────────────────────────────

def test_intent_detection_all_prompts() -> None:
    positives = [
        "draft workflow proposal",
        "create workflow proposal",
        "generate ci workflow",
        "draft ci.yml",
        "create this workflow file",
        "add this workflow file",
        "commit this workflow",
        "open PR for this workflow",
        "push the workflow to main",
        "cancel",
    ]
    for phrase in positives:
        assert is_workflow_lane_intent(phrase), f"not detected: {phrase!r}"


def test_intent_detection_negatives() -> None:
    negatives = [
        "what should I do next?",
        "show route trace",
        "check railway services",
        "why is MongoDB failed?",
        "restart vercel deployment",
        "restart pilotos-api in railway",
        "retry",
    ]
    for phrase in negatives:
        assert not is_workflow_lane_intent(phrase), f"false positive: {phrase!r}"


# ─── Proposal ────────────────────────────────────────────────────────────────

def test_draft_workflow_proposal_returns_yaml() -> None:
    result = route_workflow_lane("draft workflow proposal", session_id="lane-1")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_discovery_proposal"
    assert meta["route_id"] == "github_workflow_lane"
    assert meta["workflow_lane_stage"] == "proposal_ready"
    assert "```yaml" in body
    assert "name: CI" in body
    assert "proposal only" in body.lower()


def test_proposal_persists_state() -> None:
    route_workflow_lane("draft workflow proposal", session_id="lane-state")
    state = get_workflow_lane_state(session_id="lane-state")
    assert state is not None
    assert state["stage"] == "proposal_ready"
    assert state["file_path"] == ".github/workflows/ci.yml"
    assert state["branch"] == "add-ci-workflow"


# ─── Creation Plan ───────────────────────────────────────────────────────────

def test_create_this_workflow_file_returns_governed_plan() -> None:
    route_workflow_lane("draft workflow proposal", session_id="lane-2")
    result = route_workflow_lane("create this workflow file", session_id="lane-2")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_creation_governed_plan"
    assert meta["workflow_lane_stage"] == "creation_plan_ready"
    assert "governed workflow-file creation plan" in body
    assert "add-ci-workflow" in body
    assert "approval" in body.lower()


def test_creation_plan_without_prior_proposal() -> None:
    result = route_workflow_lane("create this workflow file", session_id="lane-no-prior")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_creation_governed_plan"
    assert "governed workflow-file creation plan" in body


# ─── Push to Main Blocked ────────────────────────────────────────────────────

def test_push_to_main_blocked() -> None:
    result = route_workflow_lane("push the workflow to main", session_id="lane-3")
    assert result is not None
    body, intent, meta = result
    assert "will not" in body
    assert "T3" in body
    assert "blocked" in body.lower()
    assert meta["route_id"] == "github_workflow_lane"


# ─── Cancel ──────────────────────────────────────────────────────────────────

def test_cancel_clears_state() -> None:
    route_workflow_lane("draft workflow proposal", session_id="lane-4")
    assert get_workflow_lane_state(session_id="lane-4") is not None

    result = route_workflow_lane("cancel", session_id="lane-4")
    assert result is not None
    body, intent, meta = result
    assert intent == "workflow_creation_cancelled"
    assert "Cancelled" in body
    assert "No file, branch, commit, push, or PR" in body
    assert get_workflow_lane_state(session_id="lane-4") is None


def test_cancel_with_no_state() -> None:
    result = route_workflow_lane("cancel", session_id="lane-no-state")
    assert result is not None
    body, intent, _meta = result
    assert intent == "workflow_lane_no_state"
    assert "No pending" in body


# ─── Hijack Prevention ───────────────────────────────────────────────────────

def test_active_thread_cannot_hijack_proposal() -> None:
    result = resolve_chat_turn("draft workflow proposal", session_id="lane-hijack-1", apply_relational_layer=False)
    assert result.intent == "workflow_discovery_proposal"
    assert result.meta.get("route_id") == "github_workflow_lane"
    assert "active operational thread" not in result.reply.lower()
    assert "Mission Control" not in result.reply


def test_generic_workflow_planner_cannot_hijack() -> None:
    result = resolve_chat_turn("create this workflow file", session_id="lane-hijack-2", apply_relational_layer=False)
    assert result.intent == "workflow_creation_governed_plan"
    assert result.meta.get("route_id") == "github_workflow_lane"
    assert "what type of workflow" not in result.reply.lower()


def test_no_llm_fallback_for_proposal() -> None:
    result = resolve_chat_turn("generate ci workflow", session_id="lane-hijack-3", apply_relational_layer=False)
    assert result.intent == "workflow_discovery_proposal"
    assert result.used_llm is False


# ─── Route Trace ─────────────────────────────────────────────────────────────

def test_route_trace_includes_workflow_lane_stage() -> None:
    resolve_chat_turn("draft workflow proposal", session_id="lane-trace", apply_relational_layer=False)
    trace = get_last_route_trace(session_id="lane-trace")
    assert trace is not None
    assert trace["route_id"] == "github_workflow_lane"
    assert trace["matched_module"] == "providers.github.workflow_lane.workflow_lane_router"
    assert trace.get("workflow_lane_stage") == "proposal_ready"


def test_show_route_trace_displays_lane_info() -> None:
    resolve_chat_turn("draft workflow proposal", session_id="lane-trace-2", apply_relational_layer=False)
    result = resolve_chat_turn("show route trace", session_id="lane-trace-2", apply_relational_layer=False)
    assert "github_workflow_lane" in result.reply
    assert "workflow_lane_router" in result.reply


# ─── Live Entrypoint Tests ───────────────────────────────────────────────────

def test_resolve_chat_turn_full_lifecycle() -> None:
    sid = "lane-lifecycle"
    r1 = resolve_chat_turn("draft workflow proposal", session_id=sid, apply_relational_layer=False)
    assert r1.intent == "workflow_discovery_proposal"
    assert "name: CI" in r1.reply

    r2 = resolve_chat_turn("create this workflow file", session_id=sid, apply_relational_layer=False)
    assert r2.intent == "workflow_creation_governed_plan"
    assert "governed workflow-file creation plan" in r2.reply

    r3 = resolve_chat_turn("push the workflow to main", session_id=sid, apply_relational_layer=False)
    assert "will not" in r3.reply
    assert "T3" in r3.reply

    r4 = resolve_chat_turn("cancel", session_id=sid, apply_relational_layer=False)
    assert r4.intent == "workflow_creation_cancelled"
    assert "No file, branch, commit, push, or PR" in r4.reply

    r5 = resolve_chat_turn("show route trace", session_id=sid, apply_relational_layer=False)
    assert "github_workflow_lane" in r5.reply


# ─── Fix 83 — Render Integrity ──────────────────────────────────────────────

def test_proposal_yaml_full_content() -> None:
    result = route_workflow_lane("draft workflow proposal", session_id="render-1")
    assert result is not None
    body, _, _ = result
    assert "workflow_dispatch" in body
    assert "validate:" in body
    assert "actions/checkout@v4" in body
    assert "Placeholder validation" in body
    assert "Detect project" in body


def test_proposal_yaml_fenced_code_block_closed() -> None:
    result = route_workflow_lane("draft workflow proposal", session_id="render-2")
    assert result is not None
    body, _, _ = result
    fences = body.count("```")
    assert fences >= 2, f"Expected >= 2 fences, got {fences}"


def test_no_governance_footer_inside_code_fence() -> None:
    result = route_workflow_lane("draft workflow proposal", session_id="render-3")
    assert result is not None
    body, _, _ = result
    yaml_start = body.index("```yaml")
    yaml_end = body.index("```", yaml_start + 7)
    yaml_section = body[yaml_start:yaml_end]
    assert "governance" not in yaml_section.lower()
    assert "approval-gated" not in yaml_section


def test_no_truncation_by_finalizer() -> None:
    r = resolve_chat_turn("draft workflow proposal", session_id="render-4", apply_relational_layer=True)
    assert "workflow_dispatch" in r.reply
    assert "validate:" in r.reply
    assert "actions/checkout@v4" in r.reply
    assert "Placeholder validation" in r.reply
    fences = r.reply.count("```")
    assert fences >= 2


def test_creation_plan_stores_full_yaml() -> None:
    route_workflow_lane("draft workflow proposal", session_id="render-5")
    route_workflow_lane("create this workflow file", session_id="render-5")
    state = get_workflow_lane_state(session_id="render-5")
    assert state is not None
    yaml = state["proposal_yaml"]
    assert "workflow_dispatch" in yaml
    assert "validate:" in yaml
    assert "Placeholder validation" in yaml
