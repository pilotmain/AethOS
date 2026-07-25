# SPDX-License-Identifier: Apache-2.0
"""FIX 180 — governed chat command invocation from handoff certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_180_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
    clear_frozen_gate_execution_request_adapter_records_for_tests,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
    clear_frozen_gate_intake_preview_records_for_tests,
)
from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
    clear_gate_routed_lane_entry_handoff_records_for_tests,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_180,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180,
    CHAT_GOVERNANCE_REQUIRED_FIX_180,
    CODE_WRITE_ENABLED_FIX_180,
    DIRECT_EXECUTION_PERFORMED_FIX_180,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
    EXECUTION_PERFORMED_FIX_180,
    FORBIDDEN_INVOCATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_180,
    GATE_EXECUTION_PERFORMED_FIX_180,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_FIX,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_INVARIANT,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_PRINCIPLES,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_ROUTE_ID,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_SCHEMA_VERSION,
    HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180,
    LANE_ADMISSION_EXECUTED_FIX_180,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_180,
    MERGE_DEPLOY_ENABLED_FIX_180,
    MUTATION_PERFORMED_FIX_180,
    PR_ACTION_ENABLED_FIX_180,
    RAILWAY_MUTATION_ENABLED_FIX_180,
    TIER_ESCALATION_ENABLED_FIX_180,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_179,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_service import (
    build_governed_chat_command_invocation_from_handoff,
    invoke_governed_chat_command_from_handoff,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_store import (
    append_governed_chat_command_invocation_from_handoff_record,
    clear_governed_chat_command_invocation_from_handoff_records_for_tests,
)
from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
    clear_human_lane_admission_decision_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_mission_control_governed_chat_command_invocation_from_handoff import _invocation_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gccifh-cert-180"


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
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
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
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()


class TestMissionControlGovernedChatCommandInvocationFromHandoffCertification:
    def test_fix_180_contract(self) -> None:
        assert GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_FIX == "FIX 180"
        assert GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_SCHEMA_VERSION == (
            "mission_control_governed_chat_command_invocation_from_handoff_v1"
        )
        assert MUTATION_PERFORMED_FIX_180 is False
        assert EXECUTION_PERFORMED_FIX_180 is False
        assert DIRECT_EXECUTION_PERFORMED_FIX_180 is False
        assert DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180 is False
        assert HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180 is False
        assert GATE_EXECUTION_PERFORMED_FIX_180 is False
        assert LANE_ENTRY_EXECUTION_PERFORMED_FIX_180 is False
        assert LANE_ADMISSION_EXECUTED_FIX_180 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_180 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180 is False
        assert TIER_ESCALATION_ENABLED_FIX_180 is False
        assert GATE_BYPASS_ENABLED_FIX_180 is False
        assert CODE_WRITE_ENABLED_FIX_180 is False
        assert PR_ACTION_ENABLED_FIX_180 is False
        assert MERGE_DEPLOY_ENABLED_FIX_180 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_180 is False
        assert CHAT_GOVERNANCE_REQUIRED_FIX_180 is True
        assert len(GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_PRINCIPLES) >= 9
        assert len(FORBIDDEN_INVOCATION_ACTIONS) >= 10
        assert "execution_request_recompute" in {a for a, _ in FORBIDDEN_INVOCATION_ACTIONS}

    def test_fix_180_composes_upstream_without_duplication(self) -> None:
        _invocation_stack(SESSION)
        result = build_governed_chat_command_invocation_from_handoff(session_id=SESSION)
        assert result.ok is True
        invocation = result.governed_chat_command_invocation_from_handoff

        assert set(invocation["fix_180_certification_requirements"]) == set(FIX_180_CERTIFICATION_REQUIREMENTS)
        assert invocation["composes_upstream_layers_not_duplicates"] is True
        assert invocation["sources"]["composes_frozen_gate_execution_request_adapter"] is True

        section_keys = set(invocation.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_179)

        upstream_read = invocation["sections"]["execution_request_upstream_read"][0]
        assert upstream_read.get("recomputed_by_fix_180") is False

        assert invocation["direct_execution_performed"] is False
        assert invocation["direct_provider_mutation_performed"] is False
        assert "invocation" in GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_INVARIANT.lower()

    def test_governed_chat_command_invocation_from_handoff_cognition_layer(self) -> None:
        _invocation_stack(SESSION)
        record, blockers = append_governed_chat_command_invocation_from_handoff_record(
            session_id=SESSION,
            kind="invocation_artifact",
            content="Invocation artifact staged for governed chat route",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False
        assert record.get("direct_provider_mutation_performed") is False

        result = build_governed_chat_command_invocation_from_handoff(session_id=SESSION)
        assert result.ok is True
        assert result.governed_chat_command_invocation_from_handoff[
            "governed_chat_command_invocation_from_handoff_cognition"
        ] is True
        assert result.governed_chat_command_invocation_from_handoff["invocation_ready"] is True

    def test_operator_api_includes_governed_chat_command_invocation_from_handoff_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governed-chat-command-invocation-from-handoff" in paths
        assert "/mission-control/governed-chat-command-invocation-from-handoff/record" in paths
        assert "/mission-control/governed-chat-command-invocation-from-handoff/invoke" in paths

    def test_invoke_routes_through_chat_governance(self) -> None:
        _invocation_stack(SESSION)
        outcome = invoke_governed_chat_command_from_handoff(session_id=SESSION)
        assert outcome.ok is True
        assert outcome.chat_governance_routed is True
        assert outcome.direct_provider_mutation is False
        assert outcome.route_id != GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_ROUTE_ID
