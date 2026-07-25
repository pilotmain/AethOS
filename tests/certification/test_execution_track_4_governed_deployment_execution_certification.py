# SPDX-License-Identifier: Apache-2.0
"""FIX 337 / EXECUTION_TRACK_4 certification."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_contract import (
    AUTONOMOUS_DEPLOYMENT_ENABLED_FIX_337,
    DEPLOYMENT_AUTHORITY_FIX_337,
    EXECUTION_TRACK_4_ID,
    EXECUTION_TRACK_4_PHASES,
    GOVERNED_DEPLOYMENT_EXECUTION_FIX,
    GOVERNED_DEPLOYMENT_EXECUTION_INVARIANT,
    GOVERNED_DEPLOYMENT_EXECUTION_ROUTE_ID,
    GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION,
    LOCAL_DEPLOYMENT_EXECUTION_EXECUTABLE_FIX_337,
    PRODUCTION_PROMOTION_AUTHORITY_FIX_337,
    ROLLBACK_AUTHORITY_FIX_337,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_service import (
    build_governed_deployment_execution,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    clear_governed_deployment_execution_records_for_tests,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_337_CERTIFICATION_REQUIREMENTS

pytestmark = pytest.mark.certification

SESSION = "et4-cert-337"


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()


class TestExecutionTrack4GovernedDeploymentExecutionCertification:
    def test_fix_337_contract(self) -> None:
        assert GOVERNED_DEPLOYMENT_EXECUTION_FIX == "FIX 337"
        assert EXECUTION_TRACK_4_ID == "EXECUTION_TRACK_4"
        assert GOVERNED_DEPLOYMENT_EXECUTION_SCHEMA_VERSION == (
            "execution_track_governed_deployment_execution_v1"
        )
        assert DEPLOYMENT_AUTHORITY_FIX_337 is False
        assert AUTONOMOUS_DEPLOYMENT_ENABLED_FIX_337 is False
        assert ROLLBACK_AUTHORITY_FIX_337 is False
        assert PRODUCTION_PROMOTION_AUTHORITY_FIX_337 is False
        assert LOCAL_DEPLOYMENT_EXECUTION_EXECUTABLE_FIX_337 is True

    def test_fix_337_execution_not_authority(self) -> None:
        result = build_governed_deployment_execution(session_id=SESSION)
        board = result.governed_deployment_execution
        assert set(board["fix_337_certification_requirements"]) == set(FIX_337_CERTIFICATION_REQUIREMENTS)
        assert board["deployment_authority"] is False
        assert "rollback" in GOVERNED_DEPLOYMENT_EXECUTION_INVARIANT

    def test_fix_337_phases_present(self) -> None:
        result = build_governed_deployment_execution(session_id=SESSION)
        sections = result.governed_deployment_execution["sections"]
        for phase in EXECUTION_TRACK_4_PHASES:
            assert sections[phase]

    def test_fix_337_certification_requirement_count(self) -> None:
        assert len(FIX_337_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_337_route_id(self) -> None:
        assert GOVERNED_DEPLOYMENT_EXECUTION_ROUTE_ID == "execution_track_governed_deployment_execution"

    def test_fix_337_local_execution_gated(self) -> None:
        result = build_governed_deployment_execution(session_id=SESSION)
        board = result.governed_deployment_execution
        assert board["local_deployment_execution_executable"] is True
        assert board["rollback_authority"] is False
