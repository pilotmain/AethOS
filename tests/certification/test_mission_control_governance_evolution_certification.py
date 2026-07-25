# SPDX-License-Identifier: Apache-2.0
"""FIX 155 — governance evolution certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_evolution.governance_evolution_contract import (
    AUTOMATIC_DOCTRINE_MIGRATION_ENABLED_FIX_155,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155,
    AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155,
    CONSTITUTIONAL_EPOCHS,
    EVOLUTION_RECOMMENDATION_EXECUTABLE,
    EVOLUTION_RECORD_KINDS,
    GOVERNANCE_EVOLUTION_FIX,
    GOVERNANCE_EVOLUTION_SCHEMA_VERSION,
    GOVERNANCE_GENERATIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_155,
    MUTATION_PERFORMED_FIX_155,
    POLICY_MUTATION_AUTHORITY_ENABLED_FIX_155,
    SELF_DIRECTED_INSTITUTIONAL_TRANSFORMATION_ENABLED_FIX_155,
    TEMPORAL_COGNITION_PRINCIPLES,
)
from aethos_core.mission_control.governance_evolution.governance_evolution_service import build_governance_evolution
from aethos_core.mission_control.governance_evolution.governance_evolution_store import (
    append_governance_evolution_record,
    clear_governance_evolution_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-evolution-cert-155"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_evolution_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_evolution_records_for_tests()


class TestMissionControlGovernanceEvolutionCertification:
    def test_fix_155_contract(self) -> None:
        assert GOVERNANCE_EVOLUTION_FIX == "FIX 155"
        assert GOVERNANCE_EVOLUTION_SCHEMA_VERSION == "mission_control_governance_evolution_v1"
        assert MUTATION_PERFORMED_FIX_155 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155 is False
        assert AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155 is False
        assert SELF_DIRECTED_INSTITUTIONAL_TRANSFORMATION_ENABLED_FIX_155 is False
        assert AUTOMATIC_DOCTRINE_MIGRATION_ENABLED_FIX_155 is False
        assert POLICY_MUTATION_AUTHORITY_ENABLED_FIX_155 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_155 is False
        assert EVOLUTION_RECOMMENDATION_EXECUTABLE is False
        assert "doctrine_era" in EVOLUTION_RECORD_KINDS
        assert len(TEMPORAL_COGNITION_PRINCIPLES) >= 8
        assert len(CONSTITUTIONAL_EPOCHS) >= 7
        assert len(GOVERNANCE_GENERATIONS) >= 3

    def test_governance_evolution_temporal_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_governance_evolution_record(
            session_id=SESSION,
            kind="doctrine_era",
            content="Advisory: constitutional governance era spans FIX 150–155 institutional stack.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_governance_evolution(session_id=SESSION)
        assert result.ok is True
        assert result.evolution["institutional_temporal_governance_cognition"] is True
        assert result.evolution["evolution_record_count"] == 1

    def test_operator_api_includes_governance_evolution_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-evolution" in paths
        assert "/mission-control/governance-evolution/record" in paths
