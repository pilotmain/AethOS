# SPDX-License-Identifier: Apache-2.0
"""FIX 295 — autonomous capability registry certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_295_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_contract import (
    AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295,
    AUTONOMOUS_CAPABILITY_REGISTRY_FIX,
    AUTONOMOUS_CAPABILITY_REGISTRY_INVARIANT,
    AUTONOMOUS_CAPABILITY_REGISTRY_PRINCIPLES,
    AUTONOMOUS_CAPABILITY_REGISTRY_ROUTE_ID,
    AUTONOMOUS_CAPABILITY_REGISTRY_SCHEMA_VERSION,
    CAPABILITY_AUTHORITY_FIX_295,
    SELF_AUTHORITY_GRANTING_ENABLED_FIX_295,
    TRUST_MUTATION_AUTHORITY_FIX_295,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface

pytestmark = pytest.mark.certification

SESSION = "mc-acr-cert-295"


class TestMissionControlAutonomousCapabilityRegistryCertification:
    def test_fix_295_contract(self) -> None:
        assert AUTONOMOUS_CAPABILITY_REGISTRY_FIX == "FIX 295"
        assert AUTONOMOUS_CAPABILITY_REGISTRY_SCHEMA_VERSION == (
            "mission_control_autonomous_capability_registry_v1"
        )
        assert CAPABILITY_AUTHORITY_FIX_295 is False
        assert SELF_AUTHORITY_GRANTING_ENABLED_FIX_295 is False
        assert AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_295 is False

    def test_fix_295_capability_not_authority(self) -> None:
        result = build_autonomous_capability_registry(session_id=SESSION)
        board = result.autonomous_capability_registry
        assert set(board["fix_295_certification_requirements"]) == set(FIX_295_CERTIFICATION_REQUIREMENTS)
        assert board["capability_authority"] is False
        assert "capability_authority" in AUTONOMOUS_CAPABILITY_REGISTRY_INVARIANT

    def test_fix_295_sections_present(self) -> None:
        result = build_autonomous_capability_registry(session_id=SESSION)
        sections = result.autonomous_capability_registry["sections"]
        assert sections["capability_registry"]
        assert sections["capability_evidence_registry"]
        assert sections["capability_maturity_dashboard"]
        assert sections["capability_drift_report"]
        assert sections["self_awareness_report"]
        assert sections["provider_capability_matrix"]
        assert sections["repository_trust_matrix"]
        assert sections["capability_dashboard"]
        assert len(AUTONOMOUS_CAPABILITY_REGISTRY_PRINCIPLES) >= 10

    def test_fix_295_certification_requirement_count(self) -> None:
        assert len(FIX_295_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_295_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_295_route_id(self) -> None:
        assert AUTONOMOUS_CAPABILITY_REGISTRY_ROUTE_ID == "mission_control_autonomous_capability_registry"

    def test_fix_295_compose_only(self) -> None:
        result = build_autonomous_capability_registry(session_id=SESSION)
        sources = result.autonomous_capability_registry["sources"]
        assert sources["pilot_reexecution_performed"] is False
        assert sources["capability_self_modification_performed"] is False
        assert sources["authority_escalation_performed"] is False
