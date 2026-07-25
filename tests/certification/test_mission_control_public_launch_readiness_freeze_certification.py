# SPDX-License-Identifier: Apache-2.0
"""FIX 314 — public launch readiness freeze certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_314_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314,
    AUTOMATIC_LAUNCH_ENABLED_FIX_314,
    LAUNCH_DECISION_AUTHORITY_FIX_314,
    LAUNCH_FREEZE_AUTHORITY_FIX_314,
    LAUNCH_READINESS_FREEZE_DOMAINS,
    PUBLIC_LAUNCH_READINESS_FREEZE_FIX,
    PUBLIC_LAUNCH_READINESS_FREEZE_INVARIANT,
    PUBLIC_LAUNCH_READINESS_FREEZE_ROUTE_ID,
    PUBLIC_LAUNCH_READINESS_FREEZE_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_314,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_service import (
    build_public_launch_readiness_freeze,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_store import (
    clear_public_launch_readiness_freeze_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-plrf-cert-314"


@pytest.fixture(autouse=True)
def _clean():
    clear_public_launch_readiness_freeze_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_public_launch_readiness_freeze_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlPublicLaunchReadinessFreezeCertification:
    def test_fix_314_contract(self) -> None:
        assert PUBLIC_LAUNCH_READINESS_FREEZE_FIX == "FIX 314"
        assert PUBLIC_LAUNCH_READINESS_FREEZE_SCHEMA_VERSION == (
            "mission_control_public_launch_readiness_freeze_v1"
        )
        assert LAUNCH_FREEZE_AUTHORITY_FIX_314 is False
        assert AUTOMATIC_LAUNCH_ENABLED_FIX_314 is False
        assert AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_314 is False
        assert LAUNCH_DECISION_AUTHORITY_FIX_314 is False

    def test_fix_314_freeze_not_authority(self) -> None:
        result = build_public_launch_readiness_freeze(session_id=SESSION)
        board = result.public_launch_readiness_freeze
        assert set(board["fix_314_certification_requirements"]) == set(FIX_314_CERTIFICATION_REQUIREMENTS)
        assert board["launch_freeze_authority"] is False
        assert "authority" in PUBLIC_LAUNCH_READINESS_FREEZE_INVARIANT

    def test_fix_314_domains_present(self) -> None:
        result = build_public_launch_readiness_freeze(session_id=SESSION)
        sections = result.public_launch_readiness_freeze["sections"]
        for key in LAUNCH_READINESS_FREEZE_DOMAINS:
            assert sections[key]

    def test_fix_314_certification_requirement_count(self) -> None:
        assert len(FIX_314_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_314_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_314_route_id(self) -> None:
        assert PUBLIC_LAUNCH_READINESS_FREEZE_ROUTE_ID == "mission_control_public_launch_readiness_freeze"

    def test_fix_314_compose_only(self) -> None:
        result = build_public_launch_readiness_freeze(session_id=SESSION)
        sources = result.public_launch_readiness_freeze["sources"]
        assert sources["composes_fix_186_through_313"] is True
        assert sources["pilot_reexecution_performed"] is False
        assert sources["launch_execution_performed"] is False
        assert sources["trust_mutation_performed"] is False
        assert sources["readiness_promotion_performed"] is False
        assert sources["customer_provisioning_performed"] is False
