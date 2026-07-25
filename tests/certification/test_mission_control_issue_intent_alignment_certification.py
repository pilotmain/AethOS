# SPDX-License-Identifier: Apache-2.0
"""FIX 184 — issue intent alignment certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_184_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_contract import (
    ALIGNMENT_VALIDATION_PERFORMED_FIX_184,
    AUTONOMOUS_AUTHORITY_ENABLED_FIX_184,
    AUTONOMOUS_FILE_SELECTION_OVERRIDE_ENABLED_FIX_184,
    AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_184,
    DIRECT_EXECUTION_PERFORMED_FIX_184,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184,
    EXECUTION_PERFORMED_FIX_184,
    FORBIDDEN_ALIGNMENT_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_184,
    ISSUE_INTENT_ALIGNMENT_FIX,
    ISSUE_INTENT_ALIGNMENT_INVARIANT,
    ISSUE_INTENT_ALIGNMENT_PRINCIPLES,
    ISSUE_INTENT_ALIGNMENT_ROUTE_ID,
    ISSUE_INTENT_ALIGNMENT_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_184,
    PATCH_EXECUTION_PERFORMED_FIX_184,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
    build_issue_intent_alignment,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_end_to_end_repo_development_pilot_harness import _pilot_harness_stack

pytestmark = pytest.mark.certification

SESSION = "mc-iia-cert-184"


class TestMissionControlIssueIntentAlignmentCertification:
    def test_fix_184_contract(self) -> None:
        assert ISSUE_INTENT_ALIGNMENT_FIX == "FIX 184"
        assert ISSUE_INTENT_ALIGNMENT_SCHEMA_VERSION == "mission_control_issue_intent_alignment_v1"
        assert MUTATION_PERFORMED_FIX_184 is False
        assert EXECUTION_PERFORMED_FIX_184 is False
        assert PATCH_EXECUTION_PERFORMED_FIX_184 is False
        assert DIRECT_EXECUTION_PERFORMED_FIX_184 is False
        assert DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184 is False
        assert AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_184 is False
        assert AUTONOMOUS_FILE_SELECTION_OVERRIDE_ENABLED_FIX_184 is False
        assert AUTONOMOUS_AUTHORITY_ENABLED_FIX_184 is False
        assert GATE_BYPASS_ENABLED_FIX_184 is False
        assert ALIGNMENT_VALIDATION_PERFORMED_FIX_184 is True
        assert len(ISSUE_INTENT_ALIGNMENT_PRINCIPLES) >= 7
        assert len(FORBIDDEN_ALIGNMENT_ACTIONS) >= 6
        assert "patch_execution" in {a for a, _ in FORBIDDEN_ALIGNMENT_ACTIONS}

    def test_fix_184_composes_fix_181_without_duplication(self) -> None:
        _pilot_harness_stack(SESSION)
        result = build_issue_intent_alignment(session_id=SESSION)
        assert result.ok is True
        board = result.issue_intent_alignment
        assert set(board["fix_184_certification_requirements"]) == set(FIX_184_CERTIFICATION_REQUIREMENTS)
        assert board["composes_upstream_layers_not_duplicates"] is True
        section_keys = set(board.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_181)
        assert board["patch_execution_performed"] is False
        assert "alignment" in ISSUE_INTENT_ALIGNMENT_INVARIANT.lower()

    def test_fix_184_alignment_sections_present(self) -> None:
        _pilot_harness_stack(SESSION)
        result = build_issue_intent_alignment(session_id=SESSION)
        sections = result.issue_intent_alignment["sections"]
        assert sections["issue_scope_extraction"]
        assert sections["patch_target_validation"]
        assert sections["alignment_assessment"]
        assert sections["escalation_rules"]

    def test_fix_184_certification_requirement_count(self) -> None:
        assert len(FIX_184_CERTIFICATION_REQUIREMENTS) >= 8

    def test_fix_184_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_184_route_id(self) -> None:
        assert ISSUE_INTENT_ALIGNMENT_ROUTE_ID == "mission_control_issue_intent_alignment"
