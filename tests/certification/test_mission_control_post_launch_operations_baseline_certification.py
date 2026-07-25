# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — post-launch operations baseline certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_316_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_contract import (
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316,
    AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316,
    AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316,
    POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316,
    POST_LAUNCH_OPERATIONS_BASELINE_DOMAINS,
    POST_LAUNCH_OPERATIONS_BASELINE_FIX,
    POST_LAUNCH_OPERATIONS_BASELINE_INVARIANT,
    POST_LAUNCH_OPERATIONS_BASELINE_ROUTE_ID,
    POST_LAUNCH_OPERATIONS_BASELINE_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_316,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_service import (
    build_post_launch_operations_baseline,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_store import (
    clear_post_launch_operations_baseline_records_for_tests,
)
from aethos_core.orgs.organizations import clear_orgs_for_tests

pytestmark = pytest.mark.certification

SESSION = "mc-plob-cert-316"


@pytest.fixture(autouse=True)
def _clean():
    clear_post_launch_operations_baseline_records_for_tests()
    clear_orgs_for_tests()
    yield
    clear_post_launch_operations_baseline_records_for_tests()
    clear_orgs_for_tests()


class TestMissionControlPostLaunchOperationsBaselineCertification:
    def test_fix_316_contract(self) -> None:
        assert POST_LAUNCH_OPERATIONS_BASELINE_FIX == "FIX 316"
        assert POST_LAUNCH_OPERATIONS_BASELINE_SCHEMA_VERSION == (
            "mission_control_post_launch_operations_baseline_v1"
        )
        assert POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316 is False
        assert AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316 is False
        assert AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316 is False
        assert AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_316 is False

    def test_fix_316_baseline_not_authority(self) -> None:
        result = build_post_launch_operations_baseline(session_id=SESSION)
        board = result.post_launch_operations_baseline
        assert set(board["fix_316_certification_requirements"]) == set(FIX_316_CERTIFICATION_REQUIREMENTS)
        assert board["post_launch_operations_authority"] is False
        assert "authority" in POST_LAUNCH_OPERATIONS_BASELINE_INVARIANT

    def test_fix_316_domains_present(self) -> None:
        result = build_post_launch_operations_baseline(session_id=SESSION)
        sections = result.post_launch_operations_baseline["sections"]
        for key in POST_LAUNCH_OPERATIONS_BASELINE_DOMAINS:
            assert sections[key]

    def test_fix_316_certification_requirement_count(self) -> None:
        assert len(FIX_316_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_316_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_316_route_id(self) -> None:
        assert POST_LAUNCH_OPERATIONS_BASELINE_ROUTE_ID == "mission_control_post_launch_operations_baseline"

    def test_fix_316_compose_only(self) -> None:
        result = build_post_launch_operations_baseline(session_id=SESSION)
        sources = result.post_launch_operations_baseline["sources"]
        assert sources["composes_fix_186_through_315"] is True
        assert sources["pilot_execution_performed"] is False
        assert sources["operational_execution_performed"] is False
        assert sources["incident_response_performed"] is False
        assert sources["customer_outreach_performed"] is False
        assert sources["deployment_actions_performed"] is False
        assert sources["rollback_actions_performed"] is False
        assert sources["trust_mutation_performed"] is False
