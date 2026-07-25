# SPDX-License-Identifier: Apache-2.0
"""FIX 150 — governance role architecture + trust boundaries."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
    append_governance_collaboration_record,
    clear_governance_collaboration_records_for_tests,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
    clear_governance_deliberation_records_for_tests,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_contract import (
    TRUST_ZONES,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_intent import (
    is_governance_role_architecture_intent,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_service import (
    build_governance_role_architecture,
)
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
    clear_governance_deliberation_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    get_settings.cache_clear()


def test_governance_role_architecture_intent():
    assert is_governance_role_architecture_intent("show governance role architecture")
    assert is_governance_role_architecture_intent("trust boundaries")
    assert not is_governance_role_architecture_intent("auto-elevate role now")


def test_governance_role_architecture_api_readonly():
    session = "mc-role-arch-150"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governance-role-architecture",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["delegated_execution_authority_enabled"] is False
    assert body["autonomous_role_elevation_enabled"] is False
    architecture = body["architecture"]
    assert architecture["schema_version"] == "mission_control_governance_role_architecture_v1"
    sections = architecture["sections"]
    assert "governance_role_taxonomy" in sections
    assert "trust_boundary_modeling" in sections
    assert "separation_of_duty_policies" in sections
    assert architecture["trust_zones"] == list(TRUST_ZONES)
    assert "Governance Role Architecture" in body["markdown"]


def test_governance_role_architecture_chat_route():
    session = "mc-role-arch-chat-150"
    _full_stack(session)
    result = resolve_chat_turn("governance topology", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_governance_role_architecture"
    assert result.meta.get("mutation_performed") == "false"
    assert "Governance Role Architecture" in result.reply


def test_governance_role_architecture_observes_collaboration_roles():
    session = "mc-role-arch-collab-150"
    _full_stack(session)
    append_governance_collaboration_record(
        session_id=session,
        kind="reviewer_assignment",
        content="Alice primary reviewer",
        reviewer_name="alice",
        reviewer_role="primary_reviewer",
    )
    result = build_governance_role_architecture(session_id=session)
    assert result.ok is True
    zones = result.architecture["sections"]["operator_trust_zones"]
    assert any(z.get("operator") == "alice" for z in zones)
    delegation = result.architecture["sections"]["governance_delegation_boundaries"]
    assert any(d.get("delegation_type") == "delegated_execution_authority" and not d.get("allowed") for d in delegation)
