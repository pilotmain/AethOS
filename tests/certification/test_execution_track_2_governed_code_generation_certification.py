# SPDX-License-Identifier: Apache-2.0
"""FIX 335 / EXECUTION_TRACK_2 certification."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_contract import (
    DEPLOYMENT_AUTHORITY_FIX_335,
    EXECUTION_TRACK_2_ID,
    EXECUTION_TRACK_2_PHASES,
    GIT_COMMIT_AUTHORITY_FIX_335,
    GIT_PUSH_AUTHORITY_FIX_335,
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_FIX,
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_INVARIANT,
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_ROUTE_ID,
    GOVERNED_CODE_GENERATION_CHANGESET_CREATION_SCHEMA_VERSION,
    LOCAL_CODE_GENERATION_EXECUTABLE_FIX_335,
    MERGE_AUTHORITY_FIX_335,
    PR_CREATION_AUTHORITY_FIX_335,
    REPOSITORY_AUTHORITY_FIX_335,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_service import (
    build_governed_code_generation_changeset_creation,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_335_CERTIFICATION_REQUIREMENTS

pytestmark = pytest.mark.certification

SESSION = "et2-cert-335"


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()


class TestExecutionTrack2GovernedCodeGenerationCertification:
    def test_fix_335_contract(self) -> None:
        assert GOVERNED_CODE_GENERATION_CHANGESET_CREATION_FIX == "FIX 335"
        assert EXECUTION_TRACK_2_ID == "EXECUTION_TRACK_2"
        assert GOVERNED_CODE_GENERATION_CHANGESET_CREATION_SCHEMA_VERSION == (
            "execution_track_governed_code_generation_changeset_creation_v1"
        )
        assert REPOSITORY_AUTHORITY_FIX_335 is False
        assert GIT_COMMIT_AUTHORITY_FIX_335 is False
        assert GIT_PUSH_AUTHORITY_FIX_335 is False
        assert PR_CREATION_AUTHORITY_FIX_335 is False
        assert MERGE_AUTHORITY_FIX_335 is False
        assert DEPLOYMENT_AUTHORITY_FIX_335 is False
        assert LOCAL_CODE_GENERATION_EXECUTABLE_FIX_335 is True

    def test_fix_335_generation_not_repository_authority(self) -> None:
        result = build_governed_code_generation_changeset_creation(session_id=SESSION)
        board = result.governed_code_generation_changeset_creation
        assert set(board["fix_335_certification_requirements"]) == set(FIX_335_CERTIFICATION_REQUIREMENTS)
        assert board["repository_authority"] is False
        assert "repository" in GOVERNED_CODE_GENERATION_CHANGESET_CREATION_INVARIANT

    def test_fix_335_phases_present(self) -> None:
        result = build_governed_code_generation_changeset_creation(session_id=SESSION)
        sections = result.governed_code_generation_changeset_creation["sections"]
        for phase in EXECUTION_TRACK_2_PHASES:
            assert sections[phase]

    def test_fix_335_certification_requirement_count(self) -> None:
        assert len(FIX_335_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_335_route_id(self) -> None:
        assert GOVERNED_CODE_GENERATION_CHANGESET_CREATION_ROUTE_ID == (
            "execution_track_governed_code_generation_changeset_creation"
        )

    def test_fix_335_local_generation_gated(self) -> None:
        result = build_governed_code_generation_changeset_creation(session_id=SESSION)
        board = result.governed_code_generation_changeset_creation
        assert board["local_code_generation_executable"] is True
        assert board["git_commit_authority"] is False
