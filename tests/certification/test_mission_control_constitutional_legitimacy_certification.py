# SPDX-License-Identifier: Apache-2.0
"""FIX 161 — constitutional legitimacy certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161,
    AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161,
    CONSTITUTIONAL_AUTHORITY_EXPANSION_ENABLED_FIX_161,
    CONSTITUTIONAL_LEGITIMACY_FIX,
    CONSTITUTIONAL_LEGITIMACY_SCHEMA_VERSION,
    GOVERNANCE_LEGITIMACY_INDICATORS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_161,
    LEGITIMACY_PRINCIPLES,
    LEGITIMACY_RECOMMENDATION_EXECUTABLE,
    LEGITIMACY_RECORD_KINDS,
    MUTATION_PERFORMED_FIX_161,
    PUBLIC_TRUST_MANIPULATION_ENABLED_FIX_161,
    SOVEREIGNTY_DELEGATION_ENABLED_FIX_161,
    STAKEHOLDER_CONFIDENCE_DIMENSIONS,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_service import (
    build_constitutional_legitimacy,
)
from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_store import (
    append_constitutional_legitimacy_record,
    clear_constitutional_legitimacy_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-legitimacy-cert-161"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_legitimacy_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_legitimacy_records_for_tests()


class TestMissionControlConstitutionalLegitimacyCertification:
    def test_fix_161_contract(self) -> None:
        assert CONSTITUTIONAL_LEGITIMACY_FIX == "FIX 161"
        assert CONSTITUTIONAL_LEGITIMACY_SCHEMA_VERSION == "mission_control_constitutional_legitimacy_v1"
        assert MUTATION_PERFORMED_FIX_161 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161 is False
        assert AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161 is False
        assert PUBLIC_TRUST_MANIPULATION_ENABLED_FIX_161 is False
        assert CONSTITUTIONAL_AUTHORITY_EXPANSION_ENABLED_FIX_161 is False
        assert SOVEREIGNTY_DELEGATION_ENABLED_FIX_161 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_161 is False
        assert LEGITIMACY_RECOMMENDATION_EXECUTABLE is False
        assert "trust_continuity_note" in LEGITIMACY_RECORD_KINDS
        assert len(LEGITIMACY_PRINCIPLES) >= 8
        assert len(GOVERNANCE_LEGITIMACY_INDICATORS) >= 4
        assert len(STAKEHOLDER_CONFIDENCE_DIMENSIONS) >= 3

    def test_constitutional_legitimacy_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_constitutional_legitimacy_record(
            session_id=SESSION,
            kind="legitimacy_indicator",
            content="Advisory: chat-governed approval continuity supports governance legitimacy.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_constitutional_legitimacy(session_id=SESSION)
        assert result.ok is True
        assert result.constitutional_legitimacy["constitutional_legitimacy_cognition"] is True
        assert result.constitutional_legitimacy["legitimacy_record_count"] == 1

    def test_operator_api_includes_constitutional_legitimacy_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/constitutional-legitimacy" in paths
        assert "/mission-control/constitutional-legitimacy/record" in paths
