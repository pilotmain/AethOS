# SPDX-License-Identifier: Apache-2.0
"""FIX 178 — frozen gate intake preview certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_178_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_178,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178,
    CODE_WRITE_ENABLED_FIX_178,
    EXECUTION_PERFORMED_FIX_178,
    FORBIDDEN_INTAKE_ACTIONS,
    FROZEN_GATE_INTAKE_PREVIEW_FIX,
    FROZEN_GATE_INTAKE_PREVIEW_INVARIANT,
    FROZEN_GATE_INTAKE_PREVIEW_PRINCIPLES,
    FROZEN_GATE_INTAKE_PREVIEW_SCHEMA_VERSION,
    GATE_BYPASS_ENABLED_FIX_178,
    GATE_EXECUTION_PERFORMED_FIX_178,
    LANE_ADMISSION_EXECUTED_FIX_178,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_178,
    MERGE_DEPLOY_ENABLED_FIX_178,
    MUTATION_PERFORMED_FIX_178,
    PR_ACTION_ENABLED_FIX_178,
    RAILWAY_MUTATION_ENABLED_FIX_178,
    TIER_ESCALATION_ENABLED_FIX_178,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_177,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_service import (
    build_frozen_gate_intake_preview,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
    append_frozen_gate_intake_preview_record,
    clear_frozen_gate_intake_preview_records_for_tests,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
    clear_gate_routed_lane_entry_handoff_records_for_tests,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
    clear_human_lane_admission_decision_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_mission_control_frozen_gate_intake_preview import _intake_preview_stack

pytestmark = pytest.mark.certification

SESSION = "mc-fgip-cert-178"


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
    clear_frozen_gate_intake_preview_records_for_tests()
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
    clear_frozen_gate_intake_preview_records_for_tests()


class TestMissionControlFrozenGateIntakePreviewCertification:
    def test_fix_178_contract(self) -> None:
        assert FROZEN_GATE_INTAKE_PREVIEW_FIX == "FIX 178"
        assert FROZEN_GATE_INTAKE_PREVIEW_SCHEMA_VERSION == "mission_control_frozen_gate_intake_preview_v1"
        assert MUTATION_PERFORMED_FIX_178 is False
        assert EXECUTION_PERFORMED_FIX_178 is False
        assert GATE_EXECUTION_PERFORMED_FIX_178 is False
        assert LANE_ENTRY_EXECUTION_PERFORMED_FIX_178 is False
        assert LANE_ADMISSION_EXECUTED_FIX_178 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_178 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178 is False
        assert TIER_ESCALATION_ENABLED_FIX_178 is False
        assert GATE_BYPASS_ENABLED_FIX_178 is False
        assert CODE_WRITE_ENABLED_FIX_178 is False
        assert PR_ACTION_ENABLED_FIX_178 is False
        assert MERGE_DEPLOY_ENABLED_FIX_178 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_178 is False
        assert len(FROZEN_GATE_INTAKE_PREVIEW_PRINCIPLES) >= 9
        assert len(FORBIDDEN_INTAKE_ACTIONS) >= 10
        assert "handoff_recompute" in {a for a, _ in FORBIDDEN_INTAKE_ACTIONS}

    def test_fix_178_composes_upstream_without_duplication(self) -> None:
        _intake_preview_stack(SESSION)
        result = build_frozen_gate_intake_preview(session_id=SESSION)
        assert result.ok is True
        preview = result.frozen_gate_intake_preview

        assert set(preview["fix_178_certification_requirements"]) == set(FIX_178_CERTIFICATION_REQUIREMENTS)
        assert preview["composes_upstream_layers_not_duplicates"] is True
        assert preview["sources"]["composes_gate_routed_lane_entry_handoff"] is True

        section_keys = set(preview.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_177)

        upstream_read = preview["sections"]["handoff_upstream_read"][0]
        assert upstream_read.get("recomputed_by_fix_178") is False

        assert preview["gate_execution_performed"] is False
        assert preview["lane_entry_execution_performed"] is False
        assert "preview" in FROZEN_GATE_INTAKE_PREVIEW_INVARIANT.lower()

    def test_frozen_gate_intake_preview_cognition_layer(self) -> None:
        _intake_preview_stack(SESSION)
        record, blockers = append_frozen_gate_intake_preview_record(
            session_id=SESSION,
            kind="intake_preview_artifact",
            content="Intake preview staged for frozen gate validation",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record.get("gate_execution_performed") is False

        result = build_frozen_gate_intake_preview(session_id=SESSION)
        assert result.ok is True
        assert result.frozen_gate_intake_preview["frozen_gate_intake_preview_cognition"] is True
        assert result.frozen_gate_intake_preview["intake_preview_ready"] is True

    def test_operator_api_includes_frozen_gate_intake_preview_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/frozen-gate-intake-preview" in paths
        assert "/mission-control/frozen-gate-intake-preview/record" in paths
