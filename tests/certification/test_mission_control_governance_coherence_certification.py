# SPDX-License-Identifier: Apache-2.0
"""FIX 153 — governance coherence certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_coherence.governance_coherence_contract import (
    AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_153,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153,
    AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153,
    COHERENCE_INTELLIGENCE_PRINCIPLES,
    COHERENCE_RECOMMENDATION_EXECUTABLE,
    COHERENCE_RECORD_KINDS,
    CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_153,
    GOVERNANCE_COHERENCE_FIX,
    GOVERNANCE_COHERENCE_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_153,
    MUTATION_PERFORMED_FIX_153,
    SELF_HEALING_GOVERNANCE_ENABLED_FIX_153,
)
from aethos_core.mission_control.governance_coherence.governance_coherence_service import build_governance_coherence
from aethos_core.mission_control.governance_coherence.governance_coherence_store import (
    append_governance_coherence_record,
    clear_governance_coherence_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-coherence-cert-153"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_coherence_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_coherence_records_for_tests()


class TestMissionControlGovernanceCoherenceCertification:
    def test_fix_153_contract(self) -> None:
        assert GOVERNANCE_COHERENCE_FIX == "FIX 153"
        assert GOVERNANCE_COHERENCE_SCHEMA_VERSION == "mission_control_governance_coherence_v1"
        assert MUTATION_PERFORMED_FIX_153 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153 is False
        assert AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_153 is False
        assert AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153 is False
        assert SELF_HEALING_GOVERNANCE_ENABLED_FIX_153 is False
        assert CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_153 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_153 is False
        assert COHERENCE_RECOMMENDATION_EXECUTABLE is False
        assert "coherence_observation" in COHERENCE_RECORD_KINDS
        assert len(COHERENCE_INTELLIGENCE_PRINCIPLES) >= 8

    def test_governance_coherence_intelligence_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_governance_coherence_record(
            session_id=SESSION,
            kind="coherence_observation",
            content="Advisory: session doctrine lacks cross-session precedent alignment.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_governance_coherence(session_id=SESSION)
        assert result.ok is True
        assert result.coherence["institutional_constitutional_coherence_intelligence"] is True
        assert result.coherence["coherence_record_count"] == 1

    def test_operator_api_includes_governance_coherence_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-coherence" in paths
        assert "/mission-control/governance-coherence/record" in paths
