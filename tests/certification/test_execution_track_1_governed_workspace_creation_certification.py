# SPDX-License-Identifier: Apache-2.0
"""FIX 334 / EXECUTION_TRACK_1 certification."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_contract import (
    CLOUD_PROVISIONING_AUTHORITY_FIX_334,
    CODE_GENERATION_AUTHORITY_FIX_334,
    DEPLOYMENT_AUTHORITY_FIX_334,
    EXECUTION_TRACK_1_ID,
    EXECUTION_TRACK_1_PHASES,
    GIT_PUSH_AUTHORITY_FIX_334,
    GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_FIX,
    GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_INVARIANT,
    GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_ROUTE_ID,
    GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_SCHEMA_VERSION,
    LOCAL_BOOTSTRAP_EXECUTABLE_FIX_334,
    PR_CREATION_AUTHORITY_FIX_334,
    TRUST_MUTATION_AUTHORITY_FIX_334,
    WORKSPACE_CREATION_AUTHORITY_FIX_334,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_service import (
    build_governed_workspace_creation_repository_bootstrap,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_334_CERTIFICATION_REQUIREMENTS

pytestmark = pytest.mark.certification

SESSION = "et1-cert-334"


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_workspace_creation_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()


class TestExecutionTrack1GovernedWorkspaceCreationCertification:
    def test_fix_334_contract(self) -> None:
        assert GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_FIX == "FIX 334"
        assert EXECUTION_TRACK_1_ID == "EXECUTION_TRACK_1"
        assert GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_SCHEMA_VERSION == (
            "execution_track_governed_workspace_creation_repository_bootstrap_v1"
        )
        assert WORKSPACE_CREATION_AUTHORITY_FIX_334 is False
        assert DEPLOYMENT_AUTHORITY_FIX_334 is False
        assert GIT_PUSH_AUTHORITY_FIX_334 is False
        assert PR_CREATION_AUTHORITY_FIX_334 is False
        assert CLOUD_PROVISIONING_AUTHORITY_FIX_334 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_334 is False
        assert CODE_GENERATION_AUTHORITY_FIX_334 is False
        assert LOCAL_BOOTSTRAP_EXECUTABLE_FIX_334 is True

    def test_fix_334_creation_not_deployment(self) -> None:
        result = build_governed_workspace_creation_repository_bootstrap(session_id=SESSION)
        board = result.governed_workspace_creation_repository_bootstrap
        assert set(board["fix_334_certification_requirements"]) == set(FIX_334_CERTIFICATION_REQUIREMENTS)
        assert board["deployment_authority"] is False
        assert "deployment" in GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_INVARIANT

    def test_fix_334_phases_present(self) -> None:
        result = build_governed_workspace_creation_repository_bootstrap(session_id=SESSION)
        sections = result.governed_workspace_creation_repository_bootstrap["sections"]
        for phase in EXECUTION_TRACK_1_PHASES:
            assert sections[phase]

    def test_fix_334_certification_requirement_count(self) -> None:
        assert len(FIX_334_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_334_route_id(self) -> None:
        assert GOVERNED_WORKSPACE_CREATION_REPOSITORY_BOOTSTRAP_ROUTE_ID == (
            "execution_track_governed_workspace_creation_repository_bootstrap"
        )

    def test_fix_334_local_bootstrap_gated(self) -> None:
        result = build_governed_workspace_creation_repository_bootstrap(session_id=SESSION)
        board = result.governed_workspace_creation_repository_bootstrap
        assert board["local_bootstrap_executable"] is True
        assert board["code_generation_authority"] is False
