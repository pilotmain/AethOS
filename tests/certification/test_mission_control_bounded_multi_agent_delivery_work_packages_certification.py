# SPDX-License-Identifier: Apache-2.0
"""FIX 168 — bounded delivery work packages certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_168,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_168,
    BOUNDED_DELIVERY_AGENT_ROLE_IDS,
    BOUNDED_DELIVERY_WORK_PACKAGES_FIX,
    BOUNDED_DELIVERY_WORK_PACKAGES_SCHEMA_VERSION,
    CODE_WRITE_ENABLED_FIX_168,
    FORBIDDEN_PACKAGE_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_168,
    MERGE_DEPLOY_ENABLED_FIX_168,
    MUTATION_PERFORMED_FIX_168,
    PR_ACTION_ENABLED_FIX_168,
    RAILWAY_MUTATION_ENABLED_FIX_168,
    WORK_PACKAGES_PRINCIPLES,
    WORK_PACKAGES_RECOMMENDATION_EXECUTABLE,
    WORK_PACKAGES_RECORD_KINDS,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
    build_bounded_delivery_work_packages,
)
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
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-wpkg-cert-168"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()


class TestMissionControlBoundedDeliveryWorkPackagesCertification:
    def test_fix_168_contract(self) -> None:
        assert BOUNDED_DELIVERY_WORK_PACKAGES_FIX == "FIX 168"
        assert BOUNDED_DELIVERY_WORK_PACKAGES_SCHEMA_VERSION == "mission_control_bounded_delivery_work_packages_v1"
        assert MUTATION_PERFORMED_FIX_168 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_168 is False
        assert AUTONOMOUS_APPROVAL_ENABLED_FIX_168 is False
        assert CODE_WRITE_ENABLED_FIX_168 is False
        assert PR_ACTION_ENABLED_FIX_168 is False
        assert MERGE_DEPLOY_ENABLED_FIX_168 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_168 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_168 is False
        assert WORK_PACKAGES_RECOMMENDATION_EXECUTABLE is False
        assert "work_package_artifact" in WORK_PACKAGES_RECORD_KINDS
        assert len(WORK_PACKAGES_PRINCIPLES) >= 8
        assert len(BOUNDED_DELIVERY_AGENT_ROLE_IDS) == 5
        assert "delivery_agent" in BOUNDED_DELIVERY_AGENT_ROLE_IDS
        assert "diff_audit_agent" in BOUNDED_DELIVERY_AGENT_ROLE_IDS
        assert len(FORBIDDEN_PACKAGE_ACTIONS) >= 4

    def test_bounded_delivery_work_packages_cognition_layer(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        append_execution_handoff_coordination_record(
            session_id=SESSION,
            kind="handoff_artifact",
            content="Handoff for bounded delivery work packages.",
        )
        record, blockers = append_bounded_delivery_work_packages_record(
            session_id=SESSION,
            kind="work_package_artifact",
            content="Advisory work packages for bounded delivery agents.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_bounded_delivery_work_packages(session_id=SESSION)
        assert result.ok is True
        assert result.bounded_delivery_work_packages["bounded_delivery_work_packages_cognition"] is True
        assert result.bounded_delivery_work_packages["work_package_record_count"] == 1
        assert result.bounded_delivery_work_packages["agent_package_count"] == 5

    def test_operator_api_includes_bounded_delivery_work_packages_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/bounded-delivery-work-packages" in paths
        assert "/mission-control/bounded-delivery-work-packages/record" in paths
