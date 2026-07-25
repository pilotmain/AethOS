# SPDX-License-Identifier: Apache-2.0
"""FIX 144 — governance simulation sandbox."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governance_simulation.governance_simulation_intent import (
    is_governance_simulation_intent,
)
from aethos_core.mission_control.governance_simulation.governance_simulation_service import run_governance_simulation
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    get_settings.cache_clear()


def test_governance_simulation_intent():
    assert is_governance_simulation_intent("run governance simulation")
    assert is_governance_simulation_intent("compare governance configurations")
    assert not is_governance_simulation_intent("apply simulation to live policy")


def test_governance_simulation_api_readonly():
    session = "mc-gov-sim-144"
    _full_stack(session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/governance-simulation", params={"session_id": session, "format": "both"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["simulation_only"] is True
    assert body["mutation_performed"] is False
    assert body["live_policy_mutation_enabled"] is False
    sim = body["simulation"]
    assert sim["schema_version"] == "mission_control_governance_simulation_v1"
    assert len(sim.get("simulations") or []) >= 1
    assert sim.get("side_by_side_comparison")
    for row in sim.get("simulations") or []:
        assert row.get("executable") is False
        assert row.get("applied_to_live_policy") is False
    assert "Governance Simulation Sandbox" in body["markdown"]


def test_governance_simulation_chat_route():
    session = "mc-gov-sim-chat-144"
    _full_stack(session)
    result = resolve_chat_turn("run governance simulation", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_governance_simulation"
    assert result.meta.get("mutation_performed") == "false"
    assert result.meta.get("simulation_only") == "true"
    assert "Governance Simulation Sandbox" in result.reply


def test_governance_simulation_single_scenario():
    session = "mc-gov-sim-one-144"
    _full_stack(session)
    result = run_governance_simulation(session_id=session, scenario_ids=["increased_quorum"])
    assert result.ok is True
    assert len(result.simulation.get("simulations") or []) == 1
