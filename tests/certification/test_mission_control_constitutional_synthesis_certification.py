# SPDX-License-Identifier: Apache-2.0
"""FIX 163 — constitutional synthesis certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_163,
    AUTONOMOUS_CONSTITUTIONAL_DECISIONS_ENABLED_FIX_163,
    CONSTITUTIONAL_LAYER_STACK,
    CONSTITUTIONAL_SYNTHESIS_FIX,
    CONSTITUTIONAL_SYNTHESIS_SCHEMA_VERSION,
    CONSTITUTIONAL_TENSION_CATALOG,
    CONSTITUTIONAL_TRADEOFF_CATALOG,
    DOCTRINE_ENFORCEMENT_ENABLED_FIX_163,
    GOVERNANCE_MUTATION_PERFORMED_FIX_163,
    LEGITIMACY_ARBITRATION_ENABLED_FIX_163,
    MUTATION_PERFORMED_FIX_163,
    SOVEREIGNTY_DELEGATION_ENABLED_FIX_163,
    SYNTHESIS_PRINCIPLES,
    SYNTHESIS_RECOMMENDATION_EXECUTABLE,
    SYNTHESIS_RECORD_KINDS,
    WORLDVIEW_SELECTION_ENABLED_FIX_163,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_service import (
    build_constitutional_synthesis,
)
from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_store import (
    append_constitutional_synthesis_record,
    clear_constitutional_synthesis_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-synthesis-cert-163"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_synthesis_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_synthesis_records_for_tests()


class TestMissionControlConstitutionalSynthesisCertification:
    def test_fix_163_contract(self) -> None:
        assert CONSTITUTIONAL_SYNTHESIS_FIX == "FIX 163"
        assert CONSTITUTIONAL_SYNTHESIS_SCHEMA_VERSION == "mission_control_constitutional_synthesis_v1"
        assert MUTATION_PERFORMED_FIX_163 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_163 is False
        assert AUTONOMOUS_CONSTITUTIONAL_DECISIONS_ENABLED_FIX_163 is False
        assert DOCTRINE_ENFORCEMENT_ENABLED_FIX_163 is False
        assert LEGITIMACY_ARBITRATION_ENABLED_FIX_163 is False
        assert WORLDVIEW_SELECTION_ENABLED_FIX_163 is False
        assert SOVEREIGNTY_DELEGATION_ENABLED_FIX_163 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_163 is False
        assert SYNTHESIS_RECOMMENDATION_EXECUTABLE is False
        assert "tension_analysis_note" in SYNTHESIS_RECORD_KINDS
        assert len(SYNTHESIS_PRINCIPLES) >= 8
        assert len(CONSTITUTIONAL_TENSION_CATALOG) >= 4
        assert len(CONSTITUTIONAL_TRADEOFF_CATALOG) >= 4
        assert len(CONSTITUTIONAL_LAYER_STACK) == 14

    def test_constitutional_synthesis_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_constitutional_synthesis_record(
            session_id=SESSION,
            kind="tension_analysis_note",
            content="Advisory: ethics and legitimacy may tension across dimensions without autonomous resolution.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_constitutional_synthesis(session_id=SESSION)
        assert result.ok is True
        assert result.constitutional_synthesis["constitutional_synthesis_cognition"] is True
        assert result.constitutional_synthesis["institutional_wisdom_cognition"] is True
        assert result.constitutional_synthesis["synthesis_record_count"] == 1

    def test_operator_api_includes_constitutional_synthesis_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/constitutional-synthesis" in paths
        assert "/mission-control/constitutional-synthesis/record" in paths
