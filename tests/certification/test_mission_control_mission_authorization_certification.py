# SPDX-License-Identifier: Apache-2.0
"""FIX 170 — mission authorization certification (governance friction contract)."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_170_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
    append_bounded_delivery_work_packages_record,
    clear_bounded_delivery_work_packages_records_for_tests,
)
from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
    append_execution_handoff_coordination_record,
    clear_execution_handoff_coordination_records_for_tests,
)
from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
    append_human_decision_board_record,
    clear_human_decision_board_records_for_tests,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_170,
    AUTONOMOUS_LANE_EXPANSION_ENABLED_FIX_170,
    FORBIDDEN_AUTHORIZATION_ACTIONS,
    FORBIDDEN_IMPLICIT_LANES,
    GATE_BYPASS_ENABLED_FIX_170,
    GOVERNANCE_MUTATION_PERFORMED_FIX_170,
    MERGE_DEPLOY_ENABLED_FIX_170,
    MISSION_AUTHORIZATION_EXECUTABLE,
    MISSION_AUTHORIZATION_FIX,
    MISSION_AUTHORIZATION_INVARIANT,
    MISSION_AUTHORIZATION_PRINCIPLES,
    MISSION_AUTHORIZATION_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_170,
    PR_OPEN_ENABLED_FIX_170,
    RAILWAY_MUTATION_ENABLED_FIX_170,
    TIER_ESCALATION_ENABLED_FIX_170,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_service import build_mission_authorization
from aethos_core.mission_control.mission_authorization.mission_authorization_store import (
    append_mission_authorization_record,
    clear_mission_authorization_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-mauth-cert-170"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()


class TestMissionControlMissionAuthorizationCertification:
    def test_fix_170_contract(self) -> None:
        assert MISSION_AUTHORIZATION_FIX == "FIX 170"
        assert MISSION_AUTHORIZATION_SCHEMA_VERSION == "mission_control_mission_authorization_v1"
        assert MUTATION_PERFORMED_FIX_170 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_170 is False
        assert AUTONOMOUS_LANE_EXPANSION_ENABLED_FIX_170 is False
        assert TIER_ESCALATION_ENABLED_FIX_170 is False
        assert GATE_BYPASS_ENABLED_FIX_170 is False
        assert PR_OPEN_ENABLED_FIX_170 is False
        assert MERGE_DEPLOY_ENABLED_FIX_170 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_170 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_170 is False
        assert MISSION_AUTHORIZATION_EXECUTABLE is False
        assert "railway_orchestration" in FORBIDDEN_IMPLICIT_LANES
        assert len(MISSION_AUTHORIZATION_PRINCIPLES) >= 8
        assert len(FORBIDDEN_AUTHORIZATION_ACTIONS) >= 6

    def test_fix_170_governance_friction_certification_requirements(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        append_execution_handoff_coordination_record(
            session_id=SESSION,
            kind="handoff_artifact",
            content="Handoff for mission authorization.",
        )
        append_bounded_delivery_work_packages_record(
            session_id=SESSION,
            kind="work_package_artifact",
            content="Work packages for authorization envelope.",
        )
        result = build_mission_authorization(session_id=SESSION)
        assert result.ok is True
        auth = result.mission_authorization

        assert set(auth["fix_170_certification_requirements"]) == set(FIX_170_CERTIFICATION_REQUIREMENTS)

        envelope = auth["sections"]["bounded_work_envelope"][-1]
        allowed = set(envelope.get("allowed_lanes") or [])
        assert "software_delivery" in allowed
        assert not allowed.intersection(set(FORBIDDEN_IMPLICIT_LANES))
        assert envelope.get("silent_lane_expansion") is False
        assert envelope.get("tier_escalation") is False
        assert envelope.get("gate_bypass") is False

        tier = auth["sections"]["tier_boundary_enforcement"][0]
        assert tier.get("tier_3_4_satisfied") is False

        for row in auth["sections"]["existing_gate_checks"]:
            assert row.get("gate_bypass") is not True
            assert row.get("authorization_bypasses_gate") is not True

        assert auth["gate_bypass_enabled"] is False
        assert auth["tier_escalation_enabled"] is False
        assert "bypass" in MISSION_AUTHORIZATION_INVARIANT.lower()

    def test_mission_authorization_cognition_layer(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        record, blockers = append_mission_authorization_record(
            session_id=SESSION,
            kind="mission_authorization_artifact",
            content="Bounded Tier 1-2 mission authorization envelope.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_mission_authorization(session_id=SESSION)
        assert result.ok is True
        assert result.mission_authorization["mission_authorization_cognition"] is True
        assert result.mission_authorization["authorization_record_count"] == 1
        assert result.mission_authorization["authorization_tier"] == "tier_1_tier_2_bounded"

    def test_operator_api_includes_mission_authorization_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/mission-authorization" in paths
        assert "/mission-control/mission-authorization/record" in paths
