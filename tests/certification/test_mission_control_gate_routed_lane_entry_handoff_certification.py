# SPDX-License-Identifier: Apache-2.0
"""FIX 177 — gate-routed lane entry handoff certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_177_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_177,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177,
    CODE_WRITE_ENABLED_FIX_177,
    EXECUTION_PERFORMED_FIX_177,
    FORBIDDEN_HANDOFF_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_177,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_FIX,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_INVARIANT,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_PRINCIPLES,
    GATE_ROUTED_LANE_ENTRY_HANDOFF_SCHEMA_VERSION,
    LANE_ADMISSION_EXECUTED_FIX_177,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_177,
    MERGE_DEPLOY_ENABLED_FIX_177,
    MUTATION_PERFORMED_FIX_177,
    PR_ACTION_ENABLED_FIX_177,
    RAILWAY_MUTATION_ENABLED_FIX_177,
    TIER_ESCALATION_ENABLED_FIX_177,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_176,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_service import (
    build_gate_routed_lane_entry_handoff,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
    append_gate_routed_lane_entry_handoff_record,
    clear_gate_routed_lane_entry_handoff_records_for_tests,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
    append_human_lane_admission_decision_record,
    clear_human_lane_admission_decision_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_mission_control_human_lane_admission_decision import _admission_decision_stack

pytestmark = pytest.mark.certification

SESSION = "mc-grleh-cert-177"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
        clear_bounded_execution_participation_records_for_tests,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
        clear_bounded_delivery_work_packages_records_for_tests,
    )
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
        clear_execution_handoff_coordination_records_for_tests,
    )
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
        clear_governed_lane_entry_recommendation_records_for_tests,
    )
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
        clear_governed_lane_readiness_board_records_for_tests,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
        clear_governed_task_execution_coordination_records_for_tests,
    )
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
        clear_gate_routed_package_outcome_review_records_for_tests,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
        clear_human_decision_board_records_for_tests,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_store import (
        clear_mission_authorization_records_for_tests,
    )
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    clear_governed_task_execution_coordination_records_for_tests()
    clear_gate_routed_package_outcome_review_records_for_tests()
    clear_governed_lane_entry_recommendation_records_for_tests()
    clear_governed_lane_readiness_board_records_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_mission_authorization_records_for_tests()
    clear_bounded_execution_participation_records_for_tests()
    clear_governed_task_execution_coordination_records_for_tests()
    clear_gate_routed_package_outcome_review_records_for_tests()
    clear_governed_lane_entry_recommendation_records_for_tests()
    clear_governed_lane_readiness_board_records_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()


def _handoff_stack(session: str) -> None:
    _admission_decision_stack(session)
    append_human_lane_admission_decision_record(
        session_id=session,
        kind="lane_admission_decision_record",
        content="admit: software_delivery via workspace_verification gate",
    )


class TestMissionControlGateRoutedLaneEntryHandoffCertification:
    def test_fix_177_contract(self) -> None:
        assert GATE_ROUTED_LANE_ENTRY_HANDOFF_FIX == "FIX 177"
        assert GATE_ROUTED_LANE_ENTRY_HANDOFF_SCHEMA_VERSION == (
            "mission_control_gate_routed_lane_entry_handoff_v1"
        )
        assert MUTATION_PERFORMED_FIX_177 is False
        assert EXECUTION_PERFORMED_FIX_177 is False
        assert LANE_ENTRY_EXECUTION_PERFORMED_FIX_177 is False
        assert LANE_ADMISSION_EXECUTED_FIX_177 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_177 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177 is False
        assert TIER_ESCALATION_ENABLED_FIX_177 is False
        assert GATE_BYPASS_ENABLED_FIX_177 is False
        assert CODE_WRITE_ENABLED_FIX_177 is False
        assert PR_ACTION_ENABLED_FIX_177 is False
        assert MERGE_DEPLOY_ENABLED_FIX_177 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_177 is False
        assert len(GATE_ROUTED_LANE_ENTRY_HANDOFF_PRINCIPLES) >= 9
        assert len(FORBIDDEN_HANDOFF_ACTIONS) >= 10
        assert "decision_recompute" in {a for a, _ in FORBIDDEN_HANDOFF_ACTIONS}

    def test_fix_177_composes_upstream_without_duplication(self) -> None:
        _handoff_stack(SESSION)
        result = build_gate_routed_lane_entry_handoff(session_id=SESSION)
        assert result.ok is True
        handoff = result.gate_routed_lane_entry_handoff

        assert set(handoff["fix_177_certification_requirements"]) == set(FIX_177_CERTIFICATION_REQUIREMENTS)
        assert handoff["composes_upstream_layers_not_duplicates"] is True
        assert handoff["sources"]["composes_human_lane_admission_decision"] is True

        section_keys = set(handoff.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_176)

        upstream_read = handoff["sections"]["human_decision_upstream_read"][0]
        assert upstream_read.get("recomputed_by_fix_177") is False

        assert handoff["lane_entry_execution_performed"] is False
        assert handoff["lane_admission_executed"] is False
        assert "handoff" in GATE_ROUTED_LANE_ENTRY_HANDOFF_INVARIANT.lower()

    def test_gate_routed_lane_entry_handoff_cognition_layer(self) -> None:
        _handoff_stack(SESSION)
        record, blockers = append_gate_routed_lane_entry_handoff_record(
            session_id=SESSION,
            kind="gate_handoff_artifact",
            content="Handoff packet staged for frozen gate validation",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record.get("lane_entry_execution_performed") is False

        result = build_gate_routed_lane_entry_handoff(session_id=SESSION)
        assert result.ok is True
        assert result.gate_routed_lane_entry_handoff["gate_routed_lane_entry_handoff_cognition"] is True
        assert result.gate_routed_lane_entry_handoff["handoff_ready"] is True

    def test_operator_api_includes_gate_routed_lane_entry_handoff_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/gate-routed-lane-entry-handoff" in paths
        assert "/mission-control/gate-routed-lane-entry-handoff/record" in paths
