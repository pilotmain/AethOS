# SPDX-License-Identifier: Apache-2.0
"""FIX 149 — multi-operator governance collaboration certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_collaboration.governance_collaboration_contract import (
    AUTOMATIC_MERGE_DEPLOY_ENABLED_FIX_149,
    AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149,
    AUTONOMOUS_ORGANIZATIONAL_DECISIONS_ENABLED_FIX_149,
    COLLABORATION_RECORD_KINDS,
    DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149,
    GOVERNANCE_COLLABORATION_FIX,
    GOVERNANCE_COLLABORATION_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_149,
    MUTATION_PERFORMED_FIX_149,
    REVIEWER_ROLES,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_service import (
    build_governance_collaboration_workspace,
)
from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
    append_governance_collaboration_record,
    clear_governance_collaboration_records_for_tests,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_service import (
    build_governance_deliberation_workspace,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-collaboration-cert-149"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_collaboration_records_for_tests()


class TestMissionControlGovernanceCollaborationCertification:
    def test_fix_149_contract(self) -> None:
        assert GOVERNANCE_COLLABORATION_FIX == "FIX 149"
        assert GOVERNANCE_COLLABORATION_SCHEMA_VERSION == "mission_control_governance_collaboration_v1"
        assert MUTATION_PERFORMED_FIX_149 is False
        assert DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149 is False
        assert AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149 is False
        assert AUTOMATIC_MERGE_DEPLOY_ENABLED_FIX_149 is False
        assert AUTONOMOUS_ORGANIZATIONAL_DECISIONS_ENABLED_FIX_149 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_149 is False
        assert "reviewer_assignment" in COLLABORATION_RECORD_KINDS
        assert "primary_reviewer" in REVIEWER_ROLES

    def test_governance_collaboration_institutional_continuity(self) -> None:
        _full_stack(SESSION)
        deliberation = build_governance_deliberation_workspace(session_id=SESSION)
        plan_id = str((deliberation.workspace or {}).get("plan_id") or "") or None
        record, blockers = append_governance_collaboration_record(
            session_id=SESSION,
            kind="reviewer_assignment",
            content="Alice assigned as primary reviewer for readiness board.",
            reviewer_name="alice",
            reviewer_role="primary_reviewer",
            plan_id=plan_id,
        )
        assert not blockers
        assert record is not None
        assert record["governance_mutation_performed"] is False

        result = build_governance_collaboration_workspace(session_id=SESSION)
        assert result.ok is True
        assert result.collaboration["institutional_collaborative_governance"] is True
        assert len(result.collaboration["sections"]["reviewer_assignments"]) == 1

    def test_operator_api_includes_governance_collaboration_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-collaboration" in paths
        assert "/mission-control/governance-collaboration/record" in paths
