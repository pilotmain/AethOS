# SPDX-License-Identifier: Apache-2.0
"""FIX 179 — frozen gate execution request adapter certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_179_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_179,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179,
    CODE_WRITE_ENABLED_FIX_179,
    COMMAND_EXECUTION_PERFORMED_FIX_179,
    EXECUTION_PERFORMED_FIX_179,
    FORBIDDEN_REQUEST_ACTIONS,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_FIX,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_INVARIANT,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_PRINCIPLES,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_SCHEMA_VERSION,
    GATE_BYPASS_ENABLED_FIX_179,
    GATE_EXECUTION_PERFORMED_FIX_179,
    LANE_ADMISSION_EXECUTED_FIX_179,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_179,
    MERGE_DEPLOY_ENABLED_FIX_179,
    MUTATION_PERFORMED_FIX_179,
    PR_ACTION_ENABLED_FIX_179,
    RAILWAY_MUTATION_ENABLED_FIX_179,
    TIER_ESCALATION_ENABLED_FIX_179,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_178,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_service import (
    build_frozen_gate_execution_request_adapter,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
    append_frozen_gate_execution_request_adapter_record,
    clear_frozen_gate_execution_request_adapter_records_for_tests,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
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
from tests.test_mission_control_frozen_gate_execution_request_adapter import _execution_request_stack

pytestmark = pytest.mark.certification

SESSION = "mc-fgera-cert-179"


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
    clear_frozen_gate_execution_request_adapter_records_for_tests()
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
    clear_frozen_gate_execution_request_adapter_records_for_tests()


class TestMissionControlFrozenGateExecutionRequestAdapterCertification:
    def test_fix_179_contract(self) -> None:
        assert FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_FIX == "FIX 179"
        assert FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_SCHEMA_VERSION == (
            "mission_control_frozen_gate_execution_request_adapter_v1"
        )
        assert MUTATION_PERFORMED_FIX_179 is False
        assert EXECUTION_PERFORMED_FIX_179 is False
        assert COMMAND_EXECUTION_PERFORMED_FIX_179 is False
        assert GATE_EXECUTION_PERFORMED_FIX_179 is False
        assert LANE_ENTRY_EXECUTION_PERFORMED_FIX_179 is False
        assert LANE_ADMISSION_EXECUTED_FIX_179 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_179 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179 is False
        assert TIER_ESCALATION_ENABLED_FIX_179 is False
        assert GATE_BYPASS_ENABLED_FIX_179 is False
        assert CODE_WRITE_ENABLED_FIX_179 is False
        assert PR_ACTION_ENABLED_FIX_179 is False
        assert MERGE_DEPLOY_ENABLED_FIX_179 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_179 is False
        assert len(FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_PRINCIPLES) >= 9
        assert len(FORBIDDEN_REQUEST_ACTIONS) >= 10
        assert "intake_preview_recompute" in {a for a, _ in FORBIDDEN_REQUEST_ACTIONS}

    def test_fix_179_composes_upstream_without_duplication(self) -> None:
        _execution_request_stack(SESSION)
        result = build_frozen_gate_execution_request_adapter(session_id=SESSION)
        assert result.ok is True
        adapter = result.frozen_gate_execution_request_adapter

        assert set(adapter["fix_179_certification_requirements"]) == set(FIX_179_CERTIFICATION_REQUIREMENTS)
        assert adapter["composes_upstream_layers_not_duplicates"] is True
        assert adapter["sources"]["composes_frozen_gate_intake_preview"] is True

        section_keys = set(adapter.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_178)

        upstream_read = adapter["sections"]["intake_preview_upstream_read"][0]
        assert upstream_read.get("recomputed_by_fix_179") is False

        assert adapter["command_execution_performed"] is False
        assert adapter["gate_execution_performed"] is False
        assert "request" in FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_INVARIANT.lower()

    def test_frozen_gate_execution_request_adapter_cognition_layer(self) -> None:
        _execution_request_stack(SESSION)
        record, blockers = append_frozen_gate_execution_request_adapter_record(
            session_id=SESSION,
            kind="execution_request_artifact",
            content="Execution request staged for workspace_verification frozen command",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record.get("command_execution_performed") is False

        result = build_frozen_gate_execution_request_adapter(session_id=SESSION)
        assert result.ok is True
        assert result.frozen_gate_execution_request_adapter["frozen_gate_execution_request_adapter_cognition"] is True
        assert result.frozen_gate_execution_request_adapter["execution_request_ready"] is True

    def test_operator_api_includes_frozen_gate_execution_request_adapter_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/frozen-gate-execution-request-adapter" in paths
        assert "/mission-control/frozen-gate-execution-request-adapter/record" in paths
