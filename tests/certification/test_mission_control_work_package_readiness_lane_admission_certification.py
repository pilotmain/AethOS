# SPDX-License-Identifier: Apache-2.0
"""FIX 169 — work package readiness + lane admission certification."""

from __future__ import annotations

import pytest

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
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_169,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_169,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169,
    CODE_WRITE_ENABLED_FIX_169,
    FORBIDDEN_ADMISSION_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_169,
    LANE_ADMISSION_PRINCIPLES,
    LANE_ADMISSION_RECOMMENDATION_EXECUTABLE,
    LANE_ADMISSION_RECORD_KINDS,
    MERGE_DEPLOY_ENABLED_FIX_169,
    MUTATION_PERFORMED_FIX_169,
    PACKAGE_LANE_MAP,
    PR_ACTION_ENABLED_FIX_169,
    RAILWAY_MUTATION_ENABLED_FIX_169,
    WORK_PACKAGE_READINESS_LANE_ADMISSION_FIX,
    WORK_PACKAGE_READINESS_LANE_ADMISSION_SCHEMA_VERSION,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_service import (
    build_work_package_readiness_lane_admission,
)
from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_store import (
    append_work_package_readiness_lane_admission_record,
    clear_work_package_readiness_lane_admission_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-adm-cert-169"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_work_package_readiness_lane_admission_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_human_decision_board_records_for_tests()
    clear_execution_handoff_coordination_records_for_tests()
    clear_bounded_delivery_work_packages_records_for_tests()
    clear_work_package_readiness_lane_admission_records_for_tests()


class TestMissionControlWorkPackageReadinessLaneAdmissionCertification:
    def test_fix_169_contract(self) -> None:
        assert WORK_PACKAGE_READINESS_LANE_ADMISSION_FIX == "FIX 169"
        assert WORK_PACKAGE_READINESS_LANE_ADMISSION_SCHEMA_VERSION == (
            "mission_control_work_package_readiness_lane_admission_v1"
        )
        assert MUTATION_PERFORMED_FIX_169 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169 is False
        assert AUTONOMOUS_EXECUTION_ENABLED_FIX_169 is False
        assert AUTONOMOUS_APPROVAL_ENABLED_FIX_169 is False
        assert AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169 is False
        assert CODE_WRITE_ENABLED_FIX_169 is False
        assert PR_ACTION_ENABLED_FIX_169 is False
        assert MERGE_DEPLOY_ENABLED_FIX_169 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_169 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_169 is False
        assert LANE_ADMISSION_RECOMMENDATION_EXECUTABLE is False
        assert "lane_admission_artifact" in LANE_ADMISSION_RECORD_KINDS
        assert len(LANE_ADMISSION_PRINCIPLES) >= 8
        assert len(PACKAGE_LANE_MAP) >= 5
        assert len(FORBIDDEN_ADMISSION_ACTIONS) >= 4

    def test_work_package_readiness_lane_admission_cognition_layer(self) -> None:
        _full_stack(SESSION)
        append_human_decision_board_record(
            session_id=SESSION,
            kind="selection_record",
            content="governed_delivery_continuation",
        )
        append_execution_handoff_coordination_record(
            session_id=SESSION,
            kind="handoff_artifact",
            content="Handoff for lane admission readiness.",
        )
        append_bounded_delivery_work_packages_record(
            session_id=SESSION,
            kind="work_package_artifact",
            content="Work packages for admission readiness evaluation.",
        )
        record, blockers = append_work_package_readiness_lane_admission_record(
            session_id=SESSION,
            kind="lane_admission_artifact",
            content="Advisory lane admission package for software delivery.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_work_package_readiness_lane_admission(session_id=SESSION)
        assert result.ok is True
        assert result.work_package_readiness_lane_admission["work_package_readiness_lane_admission_cognition"] is True
        assert result.work_package_readiness_lane_admission["lane_admission_record_count"] == 1
        assert result.work_package_readiness_lane_admission["agent_package_count"] == 5

    def test_operator_api_includes_work_package_readiness_lane_admission_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/work-package-readiness-lane-admission" in paths
        assert "/mission-control/work-package-readiness-lane-admission/record" in paths
