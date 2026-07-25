# SPDX-License-Identifier: Apache-2.0
"""FIX 159 — constitutional ethics certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159,
    AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159,
    CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_159,
    CONSTITUTIONAL_VALUE_CATALOG,
    CONSTITUTIONAL_ETHICS_FIX,
    CONSTITUTIONAL_ETHICS_SCHEMA_VERSION,
    ETHICS_PRINCIPLES,
    ETHICS_RECOMMENDATION_EXECUTABLE,
    ETHICS_RECORD_KINDS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_159,
    MORAL_PRECEDENT_CATALOG,
    MUTATION_PERFORMED_FIX_159,
    SELF_AUTHORED_ETHICS_ENABLED_FIX_159,
    VALUE_CONFLICT_PATTERNS,
    VALUE_ENFORCEMENT_AUTHORITY_ENABLED_FIX_159,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_service import (
    build_constitutional_ethics,
)
from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_store import (
    append_constitutional_ethics_record,
    clear_constitutional_ethics_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-ethics-cert-159"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_ethics_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_ethics_records_for_tests()


class TestMissionControlConstitutionalEthicsCertification:
    def test_fix_159_contract(self) -> None:
        assert CONSTITUTIONAL_ETHICS_FIX == "FIX 159"
        assert CONSTITUTIONAL_ETHICS_SCHEMA_VERSION == "mission_control_constitutional_ethics_v1"
        assert MUTATION_PERFORMED_FIX_159 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159 is False
        assert AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159 is False
        assert SELF_AUTHORED_ETHICS_ENABLED_FIX_159 is False
        assert CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_159 is False
        assert VALUE_ENFORCEMENT_AUTHORITY_ENABLED_FIX_159 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_159 is False
        assert ETHICS_RECOMMENDATION_EXECUTABLE is False
        assert "ethics_record" in ETHICS_RECORD_KINDS
        assert len(ETHICS_PRINCIPLES) >= 8
        assert len(CONSTITUTIONAL_VALUE_CATALOG) >= 4
        assert len(VALUE_CONFLICT_PATTERNS) >= 4
        assert len(MORAL_PRECEDENT_CATALOG) >= 3

    def test_constitutional_ethics_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_constitutional_ethics_record(
            session_id=SESSION,
            kind="ethics_record",
            content="Advisory: human sovereignty governs all moral tradeoff resolution.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_constitutional_ethics(session_id=SESSION)
        assert result.ok is True
        assert result.constitutional_ethics["constitutional_ethical_cognition"] is True
        assert result.constitutional_ethics["ethics_record_count"] == 1

    def test_operator_api_includes_constitutional_ethics_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/constitutional-ethics" in paths
        assert "/mission-control/constitutional-ethics/record" in paths
