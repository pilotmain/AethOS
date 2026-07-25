# SPDX-License-Identifier: Apache-2.0
"""FIX 127 — bounded multi-agent collaboration."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.multi_agent.multi_agent_contract import (
    BOUNDED_AGENT_ROLE_IDS,
    EXECUTOR_AGENT_ENABLED_FIX_127,
    MUTATION_PERFORMED_FIX_127,
)
from aethos_core.software_delivery.multi_agent.multi_agent_receipts import clear_for_tests as clear_receipts
from aethos_core.software_delivery.multi_agent.multi_agent_service import (
    is_multi_agent_collaboration_intent,
    run_agent_collaboration,
)
from aethos_core.software_delivery.multi_agent.multi_agent_store import clear_for_tests as clear_store
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as cp

    cp()
    clear_store()
    clear_receipts()
    get_settings.cache_clear()
    yield
    cp()
    clear_store()
    clear_receipts()
    get_settings.cache_clear()


def test_multi_agent_intents():
    assert is_multi_agent_collaboration_intent("run software delivery agent collaboration")
    assert is_multi_agent_collaboration_intent("run software delivery planner agent")


def test_no_executor_or_mutation():
    assert EXECUTOR_AGENT_ENABLED_FIX_127 is False
    assert MUTATION_PERFORMED_FIX_127 is False
    assert len(BOUNDED_AGENT_ROLE_IDS) == 5


def test_collaboration_requires_plan():
    result = run_agent_collaboration(
        session_id="sd-ma-no-plan",
        user_text="run software delivery agent collaboration",
    )
    assert not result.ok
    assert "issue_plan_missing" in result.blockers


def test_collaboration_flow():
    session = "sd-ma-flow-127"
    _full_stack(session)
    result = run_agent_collaboration(
        session_id=session,
        user_text="run software delivery agent collaboration",
    )
    assert result.ok
    assert result.record.get("mutation_performed") is False
    assert len(result.record.get("agent_outputs") or []) == 5
    for output in result.record["agent_outputs"]:
        assert output.get("mutation_performed") is False


def test_chat_route():
    session = "sd-ma-route-127"
    _full_stack(session)
    turn = resolve_chat_turn(
        "run software delivery agent collaboration",
        session_id=session,
        apply_relational_layer=False,
    )
    assert turn.intent == "software_delivery_agent_collaboration_completed"
    assert turn.meta.get("mutation_scope") == "multi_agent_advisory_only"
    assert "PlannerAgent" in turn.reply
