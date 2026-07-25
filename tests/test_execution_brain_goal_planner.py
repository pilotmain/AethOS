# SPDX-License-Identifier: Apache-2.0
"""Tests for execution brain goal planner and tool graph."""

from __future__ import annotations

from aethos_core.execution_brain.conversation_plan_registry import clear_conversation_plans_for_tests, load_conversation_plan
from aethos_core.execution_brain.goal_planner import plan_operational_goal
from aethos_core.execution_brain.tool_planning_graph import build_tool_planning_graph
from aethos_core.operational_session import clear_operational_sessions_for_tests
from aethos_core.operational_session.operational_session import load_operational_session
from aethos_core.operational_session.session_subject import SessionSubject


def test_deploy_goal_builds_multi_step_graph():
    subject = SessionSubject(provider="railway")
    plan = plan_operational_goal("Deploy AethOS to Railway", subject=subject, session=load_operational_session())
    assert plan is not None
    assert plan.kind == "deploy_planning"
    graph = build_tool_planning_graph(plan)
    tool_ids = [step.tool_id for step in graph.steps]
    assert "local_workspace.discover" in tool_ids
    assert "railway.validate_token" in tool_ids
    assert "railway.create_deploy_preflight" in tool_ids
    assert graph.planning_only is True


def test_readonly_goal_maps_to_fetch_logs_tool():
    subject = SessionSubject(provider="railway")
    plan = plan_operational_goal("show Railway logs", subject=subject, session=load_operational_session())
    assert plan is not None
    assert plan.kind == "readonly_execute"
    assert plan.readonly_goal is not None
    graph = build_tool_planning_graph(plan)
    assert any(step.tool_id.endswith("fetch_logs") for step in graph.steps)


def test_continue_goal_detected():
    plan = plan_operational_goal(
        "continue",
        subject=SessionSubject(provider="railway"),
        session=load_operational_session(),
    )
    assert plan is not None
    assert plan.is_continue is True
