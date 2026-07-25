# SPDX-License-Identifier: Apache-2.0
"""Orchestration honors an explicitly-named team. 'orchestrate a team: architect, developer,
tester, devops' must spawn THOSE specialists (each with a valid capability+action), not the
generic operational template — while single-role / non-team goals are unaffected."""

from __future__ import annotations

from aethos_core.agents.runtime.planner import plan_task
from aethos_core.agents.runtime.registry import validate_agent_action
from aethos_core.agents.runtime.role_planning import extract_requested_roles


def test_large_named_team_keeps_all_roles():
    # Previously capped at 5 + dropped trailing roles — must now keep all (up to 8).
    roles = extract_requested_roles(
        "orchestrate a team: an architect, a developer, a tester, a devops engineer, "
        "a security reviewer, a marketing lead and an analyst to plan and launch a tier"
    )
    assert len(roles) == 7
    assert "Marketing" in roles and "Analyst" in roles  # trailing roles no longer dropped


def test_dynamic_unknown_roles_each_become_agents():
    # Roles not in the known map should still each spawn an agent (dynamic), not collapse.
    roles = extract_requested_roles("orchestrate a team: a chef, a lawyer, and a CFO to open a restaurant")
    assert len(roles) == 3
    plan = plan_task("orchestrate a team: a chef, a lawyer, and a CFO to open a restaurant")
    assert len(plan.assignments) == 3
    for a in plan.assignments:
        assert a.action == "team_planning"
        assert validate_agent_action(a.agent_id, a.action)["allowed"]


def test_named_engineering_team_spawns_those_roles():
    plan = plan_task("orchestrate a team: one architect, one developer, one tester and one devops to build a URL shortener")
    caps = {a.agent_id for a in plan.assignments}
    assert {"code_intelligence", "dev_workspace", "qa_verification", "operations_analyst"} <= caps
    tasks = " ".join(a.task for a in plan.assignments).lower()
    for role in ("architect", "development", "qa", "devops"):
        assert role in tasks


def test_team_uses_generative_planning_action_and_passes_policy():
    # Named teams produce a generative PLAN (team_planning), not a diagnostic scan of a system
    # that may not exist yet — and every assignment must clear the policy gate.
    plan = plan_task("orchestrate a team: architect, developer, tester, devops, security to ship a feature")
    for a in plan.assignments:
        assert a.action == "team_planning", f"{a.agent_id} not generative"
        assert validate_agent_action(a.agent_id, a.action)["allowed"], f"{a.agent_id} blocked"


def test_single_role_goal_not_treated_as_team():
    plan = plan_task("analyze the developer workflow")
    # Only ≥2 named roles trigger the team path; a single mention uses the normal templates.
    assert "qa_verification" not in {a.agent_id for a in plan.assignments}


def test_article_led_roster_without_team_cue_keeps_all_roles():
    # "...launch WITH a strategist, a researcher, ... and a launch manager" — no "team" cue,
    # but the article-led enumeration must still spawn one agent per listed role (was 3/6).
    roles = extract_requested_roles(
        "Orchestrate a product launch with a strategist, a researcher, a copywriter, "
        "a growth marketer, a data analyst, and a launch manager"
    )
    assert len(roles) == 6
    assert "Strategist" in roles and "Launch Manager" in roles  # unknown roles kept as dynamic


def test_ordinary_prose_is_not_mistaken_for_a_roster():
    # A non-team request must not be parsed as a multi-agent roster.
    assert len(extract_requested_roles("restart aethos-api on railway")) == 1
