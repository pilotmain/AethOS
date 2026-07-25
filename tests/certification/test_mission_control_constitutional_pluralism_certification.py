# SPDX-License-Identifier: Apache-2.0
"""FIX 162 — constitutional pluralism certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_162,
    AUTHORITATIVE_WORLDVIEW_SELECTION_ENABLED_FIX_162,
    AUTONOMOUS_CONSTITUTIONAL_ARBITRATION_ENABLED_FIX_162,
    CONSTITUTIONAL_PLURALISM_FIX,
    CONSTITUTIONAL_PLURALISM_SCHEMA_VERSION,
    ENFORCED_IDEOLOGICAL_ALIGNMENT_ENABLED_FIX_162,
    GOVERNANCE_MUTATION_PERFORMED_FIX_162,
    GOVERNANCE_PERSPECTIVE_CATALOG,
    INSTITUTIONAL_PHILOSOPHY_CATALOG,
    MUTATION_PERFORMED_FIX_162,
    PLURALISM_PRINCIPLES,
    PLURALISM_RECOMMENDATION_EXECUTABLE,
    PLURALISM_RECORD_KINDS,
    SOVEREIGNTY_DELEGATION_ENABLED_FIX_162,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_service import (
    build_constitutional_pluralism,
)
from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_store import (
    append_constitutional_pluralism_record,
    clear_constitutional_pluralism_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-pluralism-cert-162"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_pluralism_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_pluralism_records_for_tests()


class TestMissionControlConstitutionalPluralismCertification:
    def test_fix_162_contract(self) -> None:
        assert CONSTITUTIONAL_PLURALISM_FIX == "FIX 162"
        assert CONSTITUTIONAL_PLURALISM_SCHEMA_VERSION == "mission_control_constitutional_pluralism_v1"
        assert MUTATION_PERFORMED_FIX_162 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_162 is False
        assert AUTHORITATIVE_WORLDVIEW_SELECTION_ENABLED_FIX_162 is False
        assert AUTONOMOUS_CONSTITUTIONAL_ARBITRATION_ENABLED_FIX_162 is False
        assert ENFORCED_IDEOLOGICAL_ALIGNMENT_ENABLED_FIX_162 is False
        assert SOVEREIGNTY_DELEGATION_ENABLED_FIX_162 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_162 is False
        assert PLURALISM_RECOMMENDATION_EXECUTABLE is False
        assert "perspective_mapping_note" in PLURALISM_RECORD_KINDS
        assert len(PLURALISM_PRINCIPLES) >= 8
        assert len(GOVERNANCE_PERSPECTIVE_CATALOG) >= 4
        assert len(INSTITUTIONAL_PHILOSOPHY_CATALOG) >= 4

    def test_constitutional_pluralism_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_constitutional_pluralism_record(
            session_id=SESSION,
            kind="perspective_mapping_note",
            content="Advisory: operator and institutional constitutional perspectives coexist under bounded governance.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_constitutional_pluralism(session_id=SESSION)
        assert result.ok is True
        assert result.constitutional_pluralism["constitutional_pluralism_cognition"] is True
        assert result.constitutional_pluralism["pluralism_record_count"] == 1

    def test_operator_api_includes_constitutional_pluralism_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/constitutional-pluralism" in paths
        assert "/mission-control/constitutional-pluralism/record" in paths
