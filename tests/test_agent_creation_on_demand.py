# SPDX-License-Identifier: Apache-2.0
"""On-demand agent creation — honors request, skills, and orchestration board lanes."""

from __future__ import annotations

import pytest

from aethos_core.agent_progression_memory.progression_store import clear_progression_for_tests
from aethos_core.agents.runtime.subagent_session_store import clear_subagent_sessions_for_tests, list_subagent_sessions
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.agents.runtime.role_planning import (
    attach_skills_requested,
    derive_creation_objective,
    extract_requested_roles,
    resolve_role_spec,
)
from aethos_core.agents.runtime.role_inference import infer_execution_intent
from aethos_core.operational_entity_runtime.lightweight_agent_registry import clear_operational_entities_for_tests


@pytest.fixture(autouse=True)
def _clean(monkeypatch, tmp_path):
    monkeypatch.setenv("AGENT_ARTIFACTS_DIR", str(tmp_path / "agent_artifacts"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    clear_operational_entities_for_tests()
    clear_progression_for_tests()
    clear_subagent_sessions_for_tests()
    yield
    clear_subagent_sessions_for_tests()
    get_settings.cache_clear()


def test_extract_roles_development_and_qa():
    roles = extract_requested_roles("create two agents, one development one qa, assign them skills")
    assert roles == ["Development", "QA"]


def test_no_gtm_objective_from_creation_prompt():
    objective = derive_creation_objective("create two agents, one development one qa, assign them skills")
    assert "gtm" not in objective.lower()
    assert "competitive" not in objective.lower()


def test_skills_requested_flag():
    assert attach_skills_requested("assign them skills to perform best")
    display, cap, skills = resolve_role_spec("QA", attach_skills=True)
    assert display == "QA"
    assert cap == "qa_verification"
    assert len(skills) >= 3


def test_agent_creation_spawns_board_sessions():
    session = "test-on-demand-create"
    prompt = "create two agents, one development one qa, assign them skills to perform best"
    assert infer_execution_intent(prompt)["intent"] == "agent_creation"

    result = resolve_chat_turn(prompt, session_id=session, channel="telegram")
    reply = result.reply.lower()
    assert "development" in reply
    assert "qa" in reply
    assert "gtm" not in reply
    assert "market researcher" not in reply
    assert "product strategist" not in reply
    assert "orchestration board" in reply or "live lane" in reply

    sessions = list_subagent_sessions(parent_session_id=session)
    assert len(sessions) >= 2
    labels = {str(s.get("role_label") or "").lower() for s in sessions}
    assert "development" in labels
    assert "qa" in labels
    for row in sessions:
        if str(row.get("role_label") or "").lower() == "qa":
            assert row.get("attached_skills")


def test_registry_has_no_standing_roster():
    from aethos_core.agents.runtime.registry import list_agents

    assert list_agents() == []
