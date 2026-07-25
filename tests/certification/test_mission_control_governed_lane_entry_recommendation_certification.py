# SPDX-License-Identifier: Apache-2.0
"""FIX 174 — governed lane entry recommendation certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_174_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
    clear_gate_routed_package_outcome_review_records_for_tests,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_174,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174,
    CODE_WRITE_ENABLED_FIX_174,
    EXECUTION_PERFORMED_FIX_174,
    FORBIDDEN_RECOMMENDATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_174,
    GOVERNANCE_MUTATION_PERFORMED_FIX_174,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_FIX,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_INVARIANT,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_PRINCIPLES,
    GOVERNED_LANE_ENTRY_RECOMMENDATION_SCHEMA_VERSION,
    LANE_ADMISSION_PERFORMED_FIX_174,
    MERGE_DEPLOY_ENABLED_FIX_174,
    MUTATION_PERFORMED_FIX_174,
    PR_ACTION_ENABLED_FIX_174,
    RAILWAY_MUTATION_ENABLED_FIX_174,
    TIER_ESCALATION_ENABLED_FIX_174,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_169,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_173,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_service import (
    build_governed_lane_entry_recommendation,
)
from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
    append_governed_lane_entry_recommendation_record,
    clear_governed_lane_entry_recommendation_records_for_tests,
)
from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
    append_governed_task_execution_coordination_record,
    clear_governed_task_execution_coordination_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_mission_control_gate_routed_package_outcome_review import _gate_review_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gler-cert-174"


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


class TestMissionControlGovernedLaneEntryRecommendationCertification:
    def test_fix_174_contract(self) -> None:
        assert GOVERNED_LANE_ENTRY_RECOMMENDATION_FIX == "FIX 174"
        assert GOVERNED_LANE_ENTRY_RECOMMENDATION_SCHEMA_VERSION == (
            "mission_control_governed_lane_entry_recommendation_v1"
        )
        assert MUTATION_PERFORMED_FIX_174 is False
        assert EXECUTION_PERFORMED_FIX_174 is False
        assert LANE_ADMISSION_PERFORMED_FIX_174 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_174 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174 is False
        assert TIER_ESCALATION_ENABLED_FIX_174 is False
        assert GATE_BYPASS_ENABLED_FIX_174 is False
        assert CODE_WRITE_ENABLED_FIX_174 is False
        assert PR_ACTION_ENABLED_FIX_174 is False
        assert MERGE_DEPLOY_ENABLED_FIX_174 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_174 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_174 is False
        assert len(GOVERNED_LANE_ENTRY_RECOMMENDATION_PRINCIPLES) >= 8
        assert len(FORBIDDEN_RECOMMENDATION_ACTIONS) >= 9
        assert "readiness_recompute" in {a for a, _ in FORBIDDEN_RECOMMENDATION_ACTIONS}
        assert "outcome_reclassify" in {a for a, _ in FORBIDDEN_RECOMMENDATION_ACTIONS}

    def test_fix_174_composes_upstream_without_duplication(self) -> None:
        _gate_review_stack(SESSION)
        result = build_governed_lane_entry_recommendation(session_id=SESSION)
        assert result.ok is True
        rec = result.governed_lane_entry_recommendation

        assert set(rec["fix_174_certification_requirements"]) == set(FIX_174_CERTIFICATION_REQUIREMENTS)
        assert rec["composes_upstream_layers_not_duplicates"] is True
        assert rec["sources"]["composes_work_package_readiness_lane_admission"] is True
        assert rec["sources"]["composes_gate_routed_package_outcome_review"] is True

        section_keys = set(rec.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_169)
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_173)

        readiness_read = rec["sections"]["readiness_upstream_read"][0]
        assert readiness_read.get("recomputed_by_fix_174") is False
        gate_read = rec["sections"]["gate_review_upstream_read"][0]
        assert gate_read.get("reclassified_by_fix_174") is False

        assert rec["lane_admission_performed"] is False
        assert rec["execution_performed"] is False
        assert rec["autonomous_lane_entry_enabled"] is False
        assert rec["gate_bypass_enabled"] is False
        assert "recommendation" in GOVERNED_LANE_ENTRY_RECOMMENDATION_INVARIANT.lower()

        for row in rec["sections"]["lane_entry_candidates"]:
            if row.get("candidate_id") and row.get("candidate_id") != "no-candidates":
                assert row.get("lane_admission_performed") is False
                assert row.get("lane_entry") is False

        for row in rec["sections"]["recommended_next_gate"]:
            assert row.get("gate_bypass") is not True
            assert row.get("lane_admission_performed") is not True

    def test_governed_lane_entry_recommendation_cognition_layer(self) -> None:
        _gate_review_stack(SESSION)
        record, blockers = append_governed_lane_entry_recommendation_record(
            session_id=SESSION,
            kind="lane_recommendation_artifact",
            content="Recommend lane entry without admission authority.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record.get("lane_admission_performed") is False

        result = build_governed_lane_entry_recommendation(session_id=SESSION)
        assert result.ok is True
        assert result.governed_lane_entry_recommendation["governed_lane_entry_recommendation_cognition"] is True
        assert result.governed_lane_entry_recommendation["lane_recommendation_record_count"] == 1

    def test_operator_api_includes_governed_lane_entry_recommendation_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governed-lane-entry-recommendation" in paths
        assert "/mission-control/governed-lane-entry-recommendation/record" in paths
