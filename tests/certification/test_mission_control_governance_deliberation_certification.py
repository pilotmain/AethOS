# SPDX-License-Identifier: Apache-2.0
"""FIX 148 — governance deliberation workspace certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_deliberation.governance_deliberation_contract import (
    AUTOMATIC_APPROVAL_ENABLED_FIX_148,
    AUTOMATIC_REJECTION_ENABLED_FIX_148,
    AUTONOMOUS_POLICY_EVOLUTION_ENABLED_FIX_148,
    DELEGATED_AUTHORITY_ENABLED_FIX_148,
    DELIBERATION_RECORD_KINDS,
    GOVERNANCE_DELIBERATION_FIX,
    GOVERNANCE_DELIBERATION_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_148,
    MUTATION_PERFORMED_FIX_148,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_service import (
    build_governance_deliberation_workspace,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
    append_governance_deliberation_record,
    clear_governance_deliberation_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-deliberation-cert-148"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()


class TestMissionControlGovernanceDeliberationCertification:
    def test_fix_148_contract(self) -> None:
        assert GOVERNANCE_DELIBERATION_FIX == "FIX 148"
        assert GOVERNANCE_DELIBERATION_SCHEMA_VERSION == "mission_control_governance_deliberation_v1"
        assert MUTATION_PERFORMED_FIX_148 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_148 is False
        assert AUTOMATIC_APPROVAL_ENABLED_FIX_148 is False
        assert AUTOMATIC_REJECTION_ENABLED_FIX_148 is False
        assert AUTONOMOUS_POLICY_EVOLUTION_ENABLED_FIX_148 is False
        assert DELEGATED_AUTHORITY_ENABLED_FIX_148 is False
        assert "operator_note" in DELIBERATION_RECORD_KINDS
        assert "decision_justification" in DELIBERATION_RECORD_KINDS

    def test_governance_deliberation_institutional_memory_layer(self) -> None:
        _full_stack(SESSION)
        from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
            build_mission_readiness_review,
        )

        readiness = build_mission_readiness_review(session_id=SESSION)
        plan_id = str((readiness.review or {}).get("plan_id") or "") or None
        record, blockers = append_governance_deliberation_record(
            session_id=SESSION,
            kind="rationale",
            content="Hold until workspace verification evidence is complete.",
            plan_id=plan_id,
        )
        assert not blockers
        assert record is not None
        assert record["governance_mutation_performed"] is False

        result = build_governance_deliberation_workspace(session_id=SESSION)
        assert result.ok is True
        assert result.workspace["institutional_governance_memory"] is True
        assert len(result.workspace["sections"]["rationale_capture"]) == 1

    def test_operator_api_includes_governance_deliberation_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-deliberation" in paths
        assert "/mission-control/governance-deliberation/record" in paths
