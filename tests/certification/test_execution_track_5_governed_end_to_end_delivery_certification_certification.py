# SPDX-License-Identifier: Apache-2.0
"""FIX 338 / EXECUTION_TRACK_5 certification."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_contract import (
    APPROVAL_BYPASS_AUTHORITY_FIX_338,
    AUTOMATIC_CERTIFICATION_PROMOTION_FIX_338,
    CERTIFICATION_STATUSES,
    DELIVERY_AUTHORITY_FIX_338,
    DEPLOYMENT_BYPASS_AUTHORITY_FIX_338,
    EXECUTION_TRACK_5_ID,
    EXECUTION_TRACK_5_PHASES,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_FIX,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_INVARIANT,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_ROUTE_ID,
    GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_SCHEMA_VERSION,
    LOCAL_CERTIFICATION_EXECUTABLE_FIX_338,
    TRUST_MUTATION_AUTHORITY_FIX_338,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_service import (
    build_governed_end_to_end_delivery_certification,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
    clear_governed_end_to_end_delivery_certification_records_for_tests,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    clear_governed_deployment_execution_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_338_CERTIFICATION_REQUIREMENTS

pytestmark = pytest.mark.certification

SESSION = "et5-cert-338"


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()


class TestExecutionTrack5EndToEndDeliveryCertificationCertification:
    def test_fix_338_contract(self) -> None:
        assert GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_FIX == "FIX 338"
        assert EXECUTION_TRACK_5_ID == "EXECUTION_TRACK_5"
        assert GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_SCHEMA_VERSION == (
            "execution_track_governed_end_to_end_delivery_certification_v1"
        )
        assert DELIVERY_AUTHORITY_FIX_338 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_338 is False
        assert AUTOMATIC_CERTIFICATION_PROMOTION_FIX_338 is False
        assert APPROVAL_BYPASS_AUTHORITY_FIX_338 is False
        assert DEPLOYMENT_BYPASS_AUTHORITY_FIX_338 is False
        assert LOCAL_CERTIFICATION_EXECUTABLE_FIX_338 is True

    def test_fix_338_certification_not_authority(self) -> None:
        result = build_governed_end_to_end_delivery_certification(session_id=SESSION)
        board = result.governed_end_to_end_delivery_certification
        assert set(board["fix_338_certification_requirements"]) == set(FIX_338_CERTIFICATION_REQUIREMENTS)
        assert board["delivery_authority"] is False
        assert "authority" in GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_INVARIANT

    def test_fix_338_phases_present(self) -> None:
        result = build_governed_end_to_end_delivery_certification(session_id=SESSION)
        sections = result.governed_end_to_end_delivery_certification["sections"]
        for phase in EXECUTION_TRACK_5_PHASES:
            assert sections[phase]

    def test_fix_338_certification_statuses(self) -> None:
        assert "NOT_CERTIFIED" in CERTIFICATION_STATUSES
        assert "CERTIFIED" in CERTIFICATION_STATUSES

    def test_fix_338_certification_requirement_count(self) -> None:
        assert len(FIX_338_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_338_route_id(self) -> None:
        assert GOVERNED_END_TO_END_DELIVERY_CERTIFICATION_ROUTE_ID == (
            "execution_track_governed_end_to_end_delivery_certification"
        )
