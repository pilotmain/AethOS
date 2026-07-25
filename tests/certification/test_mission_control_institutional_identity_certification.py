# SPDX-License-Identifier: Apache-2.0
"""FIX 156 — institutional identity certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.institutional_identity.institutional_identity_contract import (
    AUTOMATIC_CONSTITUTIONAL_REWRITING_ENABLED_FIX_156,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156,
    AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156,
    CONSTITUTIONAL_INTENT_LINEAGE,
    GOVERNANCE_MUTATION_PERFORMED_FIX_156,
    GOVERNANCE_SOVEREIGNTY_DELEGATED_FIX_156,
    IDENTITY_COGNITION_PRINCIPLES,
    IDENTITY_RECOMMENDATION_EXECUTABLE,
    IDENTITY_RECORD_KINDS,
    INSTITUTIONAL_IDENTITY_FIX,
    INSTITUTIONAL_IDENTITY_SCHEMA_VERSION,
    INSTITUTIONAL_MISSION_IDENTITY,
    MUTATION_PERFORMED_FIX_156,
    OPERATIONAL_PHILOSOPHY,
    SELF_AUTHORED_MISSION_CHANGES_ENABLED_FIX_156,
)
from aethos_core.mission_control.institutional_identity.institutional_identity_service import build_institutional_identity
from aethos_core.mission_control.institutional_identity.institutional_identity_store import (
    append_institutional_identity_record,
    clear_institutional_identity_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-identity-cert-156"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_institutional_identity_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_institutional_identity_records_for_tests()


class TestMissionControlInstitutionalIdentityCertification:
    def test_fix_156_contract(self) -> None:
        assert INSTITUTIONAL_IDENTITY_FIX == "FIX 156"
        assert INSTITUTIONAL_IDENTITY_SCHEMA_VERSION == "mission_control_institutional_identity_v1"
        assert MUTATION_PERFORMED_FIX_156 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156 is False
        assert AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156 is False
        assert SELF_AUTHORED_MISSION_CHANGES_ENABLED_FIX_156 is False
        assert AUTOMATIC_CONSTITUTIONAL_REWRITING_ENABLED_FIX_156 is False
        assert GOVERNANCE_SOVEREIGNTY_DELEGATED_FIX_156 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_156 is False
        assert IDENTITY_RECOMMENDATION_EXECUTABLE is False
        assert "mission_identity" in IDENTITY_RECORD_KINDS
        assert len(IDENTITY_COGNITION_PRINCIPLES) >= 8
        assert len(INSTITUTIONAL_MISSION_IDENTITY) >= 5
        assert len(CONSTITUTIONAL_INTENT_LINEAGE) >= 4
        assert len(OPERATIONAL_PHILOSOPHY) >= 4

    def test_institutional_identity_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_institutional_identity_record(
            session_id=SESSION,
            kind="mission_identity",
            content="Advisory: enduring mission is governed operational intelligence with human sovereignty.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_institutional_identity(session_id=SESSION)
        assert result.ok is True
        assert result.identity["institutional_identity_cognition"] is True
        assert result.identity["identity_record_count"] == 1

    def test_operator_api_includes_institutional_identity_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/institutional-identity" in paths
        assert "/mission-control/institutional-identity/record" in paths
