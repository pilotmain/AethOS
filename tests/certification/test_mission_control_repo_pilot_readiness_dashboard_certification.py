# SPDX-License-Identifier: Apache-2.0
"""FIX 182 — repo pilot readiness dashboard certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_182_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_contract import (
    AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182,
    DIRECT_EXECUTION_PERFORMED_FIX_182,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182,
    EXECUTION_PERFORMED_FIX_182,
    FORBIDDEN_READINESS_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_182,
    MUTATION_PERFORMED_FIX_182,
    PILOT_EXECUTION_PERFORMED_FIX_182,
    READINESS_VISIBILITY_ONLY_FIX_182,
    REPO_PILOT_READINESS_DASHBOARD_FIX,
    REPO_PILOT_READINESS_DASHBOARD_INVARIANT,
    REPO_PILOT_READINESS_DASHBOARD_PRINCIPLES,
    REPO_PILOT_READINESS_DASHBOARD_ROUTE_ID,
    REPO_PILOT_READINESS_DASHBOARD_SCHEMA_VERSION,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    build_repo_pilot_readiness_dashboard,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_store import (
    append_repo_pilot_readiness_dashboard_record,
    clear_repo_pilot_readiness_dashboard_records_for_tests,
)
from tests.test_mission_control_repo_pilot_readiness_dashboard import _readiness_stack

pytestmark = pytest.mark.certification

SESSION = "mc-rprd-cert-182"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
        clear_frozen_gate_execution_request_adapter_records_for_tests,
    )
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
        clear_frozen_gate_intake_preview_records_for_tests,
    )
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
        clear_gate_routed_lane_entry_handoff_records_for_tests,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_store import (
        clear_governed_chat_command_invocation_from_handoff_records_for_tests,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
        clear_human_lane_admission_decision_records_for_tests,
    )
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_repo_pilot_readiness_dashboard_records_for_tests()
    yield
    clear_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_repo_pilot_readiness_dashboard_records_for_tests()


class TestMissionControlRepoPilotReadinessDashboardCertification:
    def test_fix_182_contract(self) -> None:
        assert REPO_PILOT_READINESS_DASHBOARD_FIX == "FIX 182"
        assert REPO_PILOT_READINESS_DASHBOARD_SCHEMA_VERSION == (
            "mission_control_repo_pilot_readiness_dashboard_v1"
        )
        assert MUTATION_PERFORMED_FIX_182 is False
        assert EXECUTION_PERFORMED_FIX_182 is False
        assert DIRECT_EXECUTION_PERFORMED_FIX_182 is False
        assert DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182 is False
        assert PILOT_EXECUTION_PERFORMED_FIX_182 is False
        assert AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182 is False
        assert GATE_BYPASS_ENABLED_FIX_182 is False
        assert READINESS_VISIBILITY_ONLY_FIX_182 is True
        assert len(REPO_PILOT_READINESS_DASHBOARD_PRINCIPLES) >= 10
        assert len(FORBIDDEN_READINESS_ACTIONS) >= 9
        assert "pilot_execution" in {a for a, _ in FORBIDDEN_READINESS_ACTIONS}

    def test_fix_182_composes_upstream_without_duplication(self) -> None:
        _readiness_stack(SESSION)
        result = build_repo_pilot_readiness_dashboard(session_id=SESSION)
        assert result.ok is True
        dashboard = result.repo_pilot_readiness_dashboard

        assert set(dashboard["fix_182_certification_requirements"]) == set(FIX_182_CERTIFICATION_REQUIREMENTS)
        assert dashboard["composes_upstream_layers_not_duplicates"] is True
        assert dashboard["sources"]["composes_end_to_end_repo_development_pilot_harness"] is True

        section_keys = set(dashboard.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_181)

        upstream_read = dashboard["sections"]["pilot_harness_upstream_read"][0]
        assert upstream_read.get("recomputed_by_fix_182") is False

        assert dashboard["pilot_execution_performed"] is False
        assert "readiness" in REPO_PILOT_READINESS_DASHBOARD_INVARIANT.lower()

    def test_fix_182_readiness_sections_present(self) -> None:
        _readiness_stack(SESSION)
        append_repo_pilot_readiness_dashboard_record(
            session_id=SESSION,
            kind="repo_selection_note",
            content="pilotmain/AethOS",
        )
        result = build_repo_pilot_readiness_dashboard(session_id=SESSION)
        sections = result.repo_pilot_readiness_dashboard["sections"]
        for key in (
            "repo_selection_readiness",
            "issue_selection_readiness",
            "github_auth_status_readiness",
            "branch_permissions_readiness",
            "workspace_readiness",
            "verification_command_readiness",
            "pr_creation_readiness",
            "mission_control_evidence_readiness",
            "approval_friction_summary",
            "pilot_blocker_list",
        ):
            assert key in sections

    def test_fix_182_certification_requirement_count(self) -> None:
        assert len(FIX_182_CERTIFICATION_REQUIREMENTS) >= 8

    def test_fix_182_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_182_route_id(self) -> None:
        assert REPO_PILOT_READINESS_DASHBOARD_ROUTE_ID == "mission_control_repo_pilot_readiness_dashboard"
