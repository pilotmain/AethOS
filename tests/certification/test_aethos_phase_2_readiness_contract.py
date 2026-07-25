# SPDX-License-Identifier: Apache-2.0
"""FIX 124 — Phase 2 readiness contract certification."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aethos_core.phase.aethos_phase_2_readiness_contract import (
    AUTONOMOUS_SOFTWARE_DELIVERY_BOUNDARY,
    CERTIFY_EXPECTED_MIN_TESTS_FIX_124,
    CERTIFY_TEST_MODULE_COUNT_FIX_124,
    INFRA_ORCHESTRATION_INVARIANT,
    PHASE_2_ALLOWED_CAPABILITIES,
    PHASE_2_ENTRY_CRITERIA,
    PHASE_2_FORBIDDEN_CAPABILITIES,
    PHASE_2_READINESS_FIX,
    PRODUCTION_GOVERNANCE_FIX_RANGE,
    PRODUCTION_GOVERNANCE_MODULES,
    RAILWAY_PHASE_1_FREEZE_FIX,
    MISSION_CONTROL_FIX_135_SHIPPED,
    MISSION_CONTROL_FIX_136_SHIPPED,
    MISSION_CONTROL_FIX_137_SHIPPED,
    MISSION_CONTROL_FIX_137B_SHIPPED,
    MISSION_CONTROL_FIX_138_SHIPPED,
    MISSION_CONTROL_FIX_139_SHIPPED,
    MISSION_CONTROL_FIX_140_SHIPPED,
    MISSION_CONTROL_FIX_141_SHIPPED,
    MISSION_CONTROL_FIX_142_SHIPPED,
    MISSION_CONTROL_FIX_143_SHIPPED,
    MISSION_CONTROL_FIX_144_SHIPPED,
    MISSION_CONTROL_FIX_145_SHIPPED,
    MISSION_CONTROL_FIX_146_SHIPPED,
    MISSION_CONTROL_FIX_147_SHIPPED,
    MISSION_CONTROL_FIX_148_SHIPPED,
    MISSION_CONTROL_FIX_149_SHIPPED,
    MISSION_CONTROL_FIX_150_SHIPPED,
    MISSION_CONTROL_FIX_151_SHIPPED,
    MISSION_CONTROL_FIX_152_SHIPPED,
    MISSION_CONTROL_FIX_153_SHIPPED,
    MISSION_CONTROL_FIX_154_SHIPPED,
    MISSION_CONTROL_FIX_155_SHIPPED,
    MISSION_CONTROL_FIX_156_SHIPPED,
    MISSION_CONTROL_FIX_157_SHIPPED,
    MISSION_CONTROL_FIX_158_SHIPPED,
    MISSION_CONTROL_FIX_159_SHIPPED,
    MISSION_CONTROL_FIX_160_SHIPPED,
    MISSION_CONTROL_FIX_161_SHIPPED,
    MISSION_CONTROL_FIX_162_SHIPPED,
    MISSION_CONTROL_FIX_163_SHIPPED,
    MISSION_CONTROL_FIX_164_SHIPPED,
    MISSION_CONTROL_FIX_165_SHIPPED,
    MISSION_CONTROL_FIX_166_SHIPPED,
    MISSION_CONTROL_FIX_167_SHIPPED,
    MISSION_CONTROL_FIX_168_SHIPPED,
    MISSION_CONTROL_FIX_169_SHIPPED,
    MISSION_CONTROL_FIX_170_SHIPPED,
    MISSION_CONTROL_FIX_171_SHIPPED,
    MISSION_CONTROL_FIX_172_SHIPPED,
    MISSION_CONTROL_FIX_173_SHIPPED,
    MISSION_CONTROL_FIX_174_SHIPPED,
    MISSION_CONTROL_FIX_175_SHIPPED,
    MISSION_CONTROL_FIX_176_SHIPPED,
    MISSION_CONTROL_FIX_177_SHIPPED,
    MISSION_CONTROL_FIX_178_SHIPPED,
    MISSION_CONTROL_FIX_179_SHIPPED,
    MISSION_CONTROL_FIX_180_SHIPPED,
    MISSION_CONTROL_FIX_181_SHIPPED,
    MISSION_CONTROL_FIX_182_SHIPPED,
    MISSION_CONTROL_FIX_183_SHIPPED,
    MISSION_CONTROL_FIX_184_SHIPPED,
    SOFTWARE_DELIVERY_FIX_185_SHIPPED,
    MISSION_CONTROL_FIX_186_SHIPPED,
    GOVERNANCE_FRICTION_APPROVAL_PRINCIPLE_SHIPPED,
    MISSION_CONTROL_OPERATOR_CONSOLE_FROZEN,
    MISSION_CONTROL_UI_FREEZE_FIX,
    SOFTWARE_DELIVERY_FIX_126_SHIPPED,
    SOFTWARE_DELIVERY_PHASE_2_FREEZE_FIX,
    SOFTWARE_DELIVERY_PHASE_2_FROZEN,
    SOFTWARE_DELIVERY_MIN_CERT_MODULES,
    SOFTWARE_DELIVERY_MIN_TEST_COUNT,
    AGENT_EXECUTION_MAPPING,
)

pytestmark = pytest.mark.certification

REPO_ROOT = Path(__file__).resolve().parents[2]


def _certify_modules_from_makefile() -> list[str]:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    for line in makefile.splitlines():
        if "tests/certification/test_aethos_core_certification.py" in line:
            return [part for part in line.split() if part.startswith("tests/certification/")]
    raise AssertionError("certify target not found in Makefile")


class TestAethosPhase2ReadinessContract:
    def test_fix_124_contract_identity(self) -> None:
        assert PHASE_2_READINESS_FIX == "FIX 124"
        assert RAILWAY_PHASE_1_FREEZE_FIX == "FIX 116"
        assert PRODUCTION_GOVERNANCE_FIX_RANGE == "FIX 117–FIX 123"

    def test_production_governance_modules_frozen(self) -> None:
        assert len(PRODUCTION_GOVERNANCE_MODULES) == 7
        assert "production_incident_command" in PRODUCTION_GOVERNANCE_MODULES
        assert "production_rollout_orchestration" in PRODUCTION_GOVERNANCE_MODULES

    def test_phase_2_allowed_vs_forbidden_disjoint(self) -> None:
        allowed = set(PHASE_2_ALLOWED_CAPABILITIES)
        forbidden = set(PHASE_2_FORBIDDEN_CAPABILITIES)
        assert not allowed.intersection(forbidden)

    def test_forbidden_includes_live_production(self) -> None:
        assert "live_production_railway_forward" in PHASE_2_FORBIDDEN_CAPABILITIES
        assert "autonomous_production_rollout_promotion" in PHASE_2_FORBIDDEN_CAPABILITIES

    def test_agent_execution_mapping_complete(self) -> None:
        assert set(AGENT_EXECUTION_MAPPING.keys()) == {"tool_loop", "hermes", "pi"}
        for detail in AGENT_EXECUTION_MAPPING.values():
            assert "governed" in detail.lower() or "orchestration" in detail.lower()

    def test_entry_criteria_and_invariants(self) -> None:
        assert "make_certify_pass" in PHASE_2_ENTRY_CRITERIA
        assert "production_governance_frozen" in PHASE_2_ENTRY_CRITERIA
        assert "software_delivery_loop_frozen" in PHASE_2_ENTRY_CRITERIA
        assert "mission_control_operator_console_frozen" in PHASE_2_ENTRY_CRITERIA
        assert MISSION_CONTROL_OPERATOR_CONSOLE_FROZEN is True
        assert MISSION_CONTROL_FIX_135_SHIPPED is True
        assert MISSION_CONTROL_FIX_136_SHIPPED is True
        assert MISSION_CONTROL_UI_FREEZE_FIX == "FIX 135"
        assert SOFTWARE_DELIVERY_PHASE_2_FROZEN is True
        assert SOFTWARE_DELIVERY_FIX_126_SHIPPED is True
        assert SOFTWARE_DELIVERY_PHASE_2_FREEZE_FIX == "FIX 126"
        assert SOFTWARE_DELIVERY_MIN_CERT_MODULES == 19
        assert SOFTWARE_DELIVERY_MIN_TEST_COUNT == 61
        assert "infra" in INFRA_ORCHESTRATION_INVARIANT.lower()
        assert "human review" in AUTONOMOUS_SOFTWARE_DELIVERY_BOUNDARY.lower()
        assert GOVERNANCE_FRICTION_APPROVAL_PRINCIPLE_SHIPPED is True
        assert MISSION_CONTROL_FIX_181_SHIPPED is True
        assert MISSION_CONTROL_FIX_182_SHIPPED is True
        assert MISSION_CONTROL_FIX_183_SHIPPED is True
        assert MISSION_CONTROL_FIX_184_SHIPPED is True
        assert SOFTWARE_DELIVERY_FIX_185_SHIPPED is True
        assert MISSION_CONTROL_FIX_186_SHIPPED is True

    def test_certify_module_count_matches_makefile(self) -> None:
        modules = _certify_modules_from_makefile()
        assert len(modules) == CERTIFY_TEST_MODULE_COUNT_FIX_124
        assert "tests/certification/test_aethos_phase_2_readiness_contract.py" in modules
        assert "tests/certification/test_software_delivery_issue_plan_certification.py" in modules
        assert "tests/certification/test_software_delivery_branch_orchestration_certification.py" in modules
        assert "tests/certification/test_software_delivery_patch_proposal_certification.py" in modules
        assert "tests/certification/test_software_delivery_workspace_application_certification.py" in modules
        assert "tests/certification/test_software_delivery_workspace_verification_certification.py" in modules
        assert "tests/certification/test_software_delivery_pr_draft_certification.py" in modules
        assert "tests/certification/test_software_delivery_github_pr_preflight_certification.py" in modules
        assert "tests/certification/test_software_delivery_branch_push_certification.py" in modules
        assert "tests/certification/test_software_delivery_github_pr_open_certification.py" in modules
        assert "tests/certification/test_software_delivery_phase_2_freeze_certification.py" in modules
        assert "tests/certification/test_software_delivery_multi_agent_certification.py" in modules
        assert "tests/certification/test_mission_control_cross_lane_certification.py" in modules
        assert "tests/certification/test_mission_control_ui_action_safety_certification.py" in modules
        assert "tests/certification/test_mission_control_ui_freeze_certification.py" in modules
        assert "tests/certification/test_mission_control_evidence_bundle_certification.py" in modules
        assert "tests/certification/test_mission_control_job_replay_certification.py" in modules
        assert "tests/certification/test_mission_control_rerun_plan_certification.py" in modules
        assert "tests/certification/test_mission_control_operational_memory_certification.py" in modules
        assert "tests/certification/test_mission_control_cross_session_memory_certification.py" in modules
        assert "tests/certification/test_mission_control_knowledge_spaces_certification.py" in modules
        assert "tests/certification/test_mission_control_operator_guidance_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_insights_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_simulation_certification.py" in modules
        assert "tests/certification/test_mission_control_mission_strategy_certification.py" in modules
        assert "tests/certification/test_mission_control_mission_orchestration_certification.py" in modules
        assert "tests/certification/test_mission_control_mission_readiness_review_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_deliberation_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_collaboration_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_role_architecture_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_doctrine_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_policy_interpretation_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_coherence_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_resilience_certification.py" in modules
        assert "tests/certification/test_mission_control_governance_evolution_certification.py" in modules
        assert "tests/certification/test_mission_control_institutional_identity_certification.py" in modules
        assert "tests/certification/test_mission_control_institutional_external_relations_certification.py" in modules
        assert "tests/certification/test_mission_control_institutional_existential_risk_certification.py" in modules
        assert "tests/certification/test_mission_control_constitutional_ethics_certification.py" in modules
        assert "tests/certification/test_mission_control_constitutional_audit_certification.py" in modules
        assert "tests/certification/test_mission_control_constitutional_legitimacy_certification.py" in modules
        assert "tests/certification/test_mission_control_constitutional_pluralism_certification.py" in modules
        assert "tests/certification/test_mission_control_constitutional_synthesis_certification.py" in modules
        assert "tests/certification/test_mission_control_mission_planning_certification.py" in modules
        assert "tests/certification/test_mission_control_mission_planning_deliberation_certification.py" in modules
        assert "tests/certification/test_mission_control_human_decision_board_certification.py" in modules
        assert "tests/certification/test_mission_control_execution_handoff_coordination_certification.py" in modules
        assert "tests/certification/test_mission_control_bounded_multi_agent_delivery_work_packages_certification.py" in modules
        assert "tests/certification/test_mission_control_work_package_readiness_lane_admission_certification.py" in modules
        assert "tests/certification/test_governance_friction_approval_principle_certification.py" in modules
        assert "tests/certification/test_mission_control_mission_authorization_certification.py" in modules
        assert "tests/certification/test_mission_control_bounded_execution_participation_certification.py" in modules
        assert "tests/certification/test_mission_control_governed_task_execution_coordination_certification.py" in modules
        assert "tests/certification/test_mission_control_gate_routed_package_outcome_review_certification.py" in modules
        assert "tests/certification/test_mission_control_governed_lane_entry_recommendation_certification.py" in modules
        assert "tests/certification/test_mission_control_governed_lane_readiness_board_certification.py" in modules
        assert "tests/certification/test_mission_control_human_lane_admission_decision_certification.py" in modules
        assert "tests/certification/test_mission_control_gate_routed_lane_entry_handoff_certification.py" in modules
        assert "tests/certification/test_mission_control_frozen_gate_intake_preview_certification.py" in modules
        assert "tests/certification/test_mission_control_frozen_gate_execution_request_adapter_certification.py" in modules
        assert "tests/certification/test_mission_control_governed_chat_command_invocation_from_handoff_certification.py" in modules
        assert "tests/certification/test_mission_control_end_to_end_repo_development_pilot_harness_certification.py" in modules
        assert "tests/certification/test_mission_control_repo_pilot_readiness_dashboard_certification.py" in modules
        assert "tests/certification/test_mission_control_pilot_validation_trust_board_certification.py" in modules
        assert "tests/certification/test_mission_control_issue_intent_alignment_certification.py" in modules
        assert "tests/certification/test_issue_intake_scope_fidelity_certification.py" in modules
        assert "tests/certification/test_mission_control_dogfood_pilot_trust_report_freeze_certification.py" in modules
        assert len(modules) >= SOFTWARE_DELIVERY_MIN_CERT_MODULES

    def test_certify_collects_minimum_test_count(self) -> None:
        modules = _certify_modules_from_makefile()
        import os
        import re

        env = os.environ.copy()
        env["AETHOS_CERTIFICATION_MODE"] = "true"
        result = subprocess.run(
            ["python", "-m", "pytest", *modules, "--collect-only"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        match = re.search(r"(\d+)\s+tests?\s+collected", result.stdout + result.stderr)
        assert match is not None, result.stdout + result.stderr
        assert int(match.group(1)) >= CERTIFY_EXPECTED_MIN_TESTS_FIX_124
