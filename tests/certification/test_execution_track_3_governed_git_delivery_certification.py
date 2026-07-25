# SPDX-License-Identifier: Apache-2.0
"""FIX 336 / EXECUTION_TRACK_3 certification."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_contract import (
    DEPLOYMENT_AUTHORITY_FIX_336,
    EXECUTION_TRACK_3_ID,
    EXECUTION_TRACK_3_PHASES,
    GOVERNED_GIT_DELIVERY_FIX,
    GOVERNED_GIT_DELIVERY_INVARIANT,
    GOVERNED_GIT_DELIVERY_ROUTE_ID,
    GOVERNED_GIT_DELIVERY_SCHEMA_VERSION,
    LOCAL_GIT_DELIVERY_EXECUTABLE_FIX_336,
    MERGE_AUTHORITY_FIX_336,
    ROLLBACK_AUTHORITY_FIX_336,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_service import (
    build_governed_git_delivery,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.governance.governance_friction_approval_contract import FIX_336_CERTIFICATION_REQUIREMENTS

pytestmark = pytest.mark.certification

SESSION = "et3-cert-336"


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()


class TestExecutionTrack3GovernedGitDeliveryCertification:
    def test_fix_336_contract(self) -> None:
        assert GOVERNED_GIT_DELIVERY_FIX == "FIX 336"
        assert EXECUTION_TRACK_3_ID == "EXECUTION_TRACK_3"
        assert GOVERNED_GIT_DELIVERY_SCHEMA_VERSION == "execution_track_governed_git_delivery_v1"
        assert MERGE_AUTHORITY_FIX_336 is False
        assert DEPLOYMENT_AUTHORITY_FIX_336 is False
        assert ROLLBACK_AUTHORITY_FIX_336 is False
        assert LOCAL_GIT_DELIVERY_EXECUTABLE_FIX_336 is True

    def test_fix_336_delivery_not_merge(self) -> None:
        result = build_governed_git_delivery(session_id=SESSION)
        board = result.governed_git_delivery
        assert set(board["fix_336_certification_requirements"]) == set(FIX_336_CERTIFICATION_REQUIREMENTS)
        assert board["merge_authority"] is False
        assert "merge" in GOVERNED_GIT_DELIVERY_INVARIANT

    def test_fix_336_phases_present(self) -> None:
        result = build_governed_git_delivery(session_id=SESSION)
        sections = result.governed_git_delivery["sections"]
        for phase in EXECUTION_TRACK_3_PHASES:
            assert sections[phase]

    def test_fix_336_certification_requirement_count(self) -> None:
        assert len(FIX_336_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_336_route_id(self) -> None:
        assert GOVERNED_GIT_DELIVERY_ROUTE_ID == "execution_track_governed_git_delivery"

    def test_fix_336_local_delivery_gated(self) -> None:
        result = build_governed_git_delivery(session_id=SESSION)
        board = result.governed_git_delivery
        assert board["local_git_delivery_executable"] is True
        assert board["merge_authority"] is False
