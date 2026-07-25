# SPDX-License-Identifier: Apache-2.0
"""FIX 181 — end-to-end repo development pilot harness certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_181_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
    AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
    CHAT_GOVERNANCE_REQUIRED_FIX_181,
    DEPLOY_ENABLED_FIX_181,
    DIRECT_EXECUTION_PERFORMED_FIX_181,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_FIX,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_INVARIANT,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_PRINCIPLES,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_ROUTE_ID,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_181,
    FORBIDDEN_PILOT_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_181,
    MERGE_ENABLED_FIX_181,
    MUTATION_PERFORMED_FIX_181,
    PRODUCTION_COUPLING_ENABLED_FIX_181,
    RAILWAY_MUTATION_ENABLED_FIX_181,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_180,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
    run_end_to_end_repo_development_pilot,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    append_end_to_end_repo_development_pilot_harness_record,
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_end_to_end_repo_development_pilot_harness import _pilot_harness_stack

pytestmark = pytest.mark.certification

SESSION = "mc-e2erpdph-cert-181"


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
    yield
    clear_for_tests()
    clear_human_lane_admission_decision_records_for_tests()
    clear_gate_routed_lane_entry_handoff_records_for_tests()
    clear_frozen_gate_intake_preview_records_for_tests()
    clear_frozen_gate_execution_request_adapter_records_for_tests()
    clear_governed_chat_command_invocation_from_handoff_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()


class TestMissionControlEndToEndRepoDevelopmentPilotHarnessCertification:
    def test_fix_181_contract(self) -> None:
        assert END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_FIX == "FIX 181"
        assert END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_SCHEMA_VERSION == (
            "mission_control_end_to_end_repo_development_pilot_harness_v1"
        )
        assert MUTATION_PERFORMED_FIX_181 is False
        assert EXECUTION_PERFORMED_FIX_181 is False
        assert DIRECT_EXECUTION_PERFORMED_FIX_181 is False
        assert DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181 is False
        assert AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181 is False
        assert GATE_BYPASS_ENABLED_FIX_181 is False
        assert MERGE_ENABLED_FIX_181 is False
        assert DEPLOY_ENABLED_FIX_181 is False
        assert RAILWAY_MUTATION_ENABLED_FIX_181 is False
        assert PRODUCTION_COUPLING_ENABLED_FIX_181 is False
        assert CHAT_GOVERNANCE_REQUIRED_FIX_181 is True
        assert len(END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_PRINCIPLES) >= 10
        assert len(FORBIDDEN_PILOT_ACTIONS) >= 10
        assert "multi_repo_pilot" in {a for a, _ in FORBIDDEN_PILOT_ACTIONS}

    def test_fix_181_composes_upstream_without_duplication(self) -> None:
        _pilot_harness_stack(SESSION)
        result = build_end_to_end_repo_development_pilot_harness(session_id=SESSION)
        assert result.ok is True
        harness = result.end_to_end_repo_development_pilot_harness

        assert set(harness["fix_181_certification_requirements"]) == set(FIX_181_CERTIFICATION_REQUIREMENTS)
        assert harness["composes_upstream_layers_not_duplicates"] is True
        assert harness["sources"]["composes_governed_chat_command_invocation_from_handoff"] is True

        section_keys = set(harness.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_180)

        upstream_read = harness["sections"]["handoff_invocation_upstream_read"][0]
        assert upstream_read.get("recomputed_by_fix_181") is False

        assert harness["autonomous_pipeline_execution_enabled"] is False
        assert harness["railway_mutation_enabled"] is False
        assert "pilot" in END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_INVARIANT.lower()

    def test_fix_181_stage_matrix_and_evidence_capture(self) -> None:
        _pilot_harness_stack(SESSION)
        append_end_to_end_repo_development_pilot_harness_record(
            session_id=SESSION,
            kind="pilot_artifact",
            content="pilotmain/AethOS#80 bounded documentation pilot",
        )
        result = build_end_to_end_repo_development_pilot_harness(session_id=SESSION)
        sections = result.end_to_end_repo_development_pilot_harness["sections"]
        assert sections["pilot_stage_status_matrix"]
        assert sections["mission_control_timeline_capture"]
        assert sections["evidence_bundle_capture"]
        assert sections["approval_friction_verification"]

    def test_fix_181_run_produces_pilot_report(self) -> None:
        _pilot_harness_stack(SESSION)
        outcome = run_end_to_end_repo_development_pilot(session_id=SESSION)
        assert outcome.chat_governance_routed is True
        assert outcome.autonomous_pipeline_execution is False
        report = outcome.pilot_report
        assert report.get("pilot_harness_not_autonomous_execution") is True
        assert report.get("hidden_provider_mutation_detected") is False
        assert report.get("merge_performed") is False

    def test_fix_181_certification_requirement_count(self) -> None:
        assert len(FIX_181_CERTIFICATION_REQUIREMENTS) >= 8

    def test_fix_181_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_181_route_id(self) -> None:
        assert END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_ROUTE_ID == (
            "mission_control_end_to_end_repo_development_pilot_harness"
        )
