# SPDX-License-Identifier: Apache-2.0
"""FIX 157 — institutional external relations certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157,
    AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157,
    AUTONOMOUS_PROVIDER_ALIGNMENT_ENABLED_FIX_157,
    CONSTITUTIONAL_BOUNDARIES,
    EXTERNAL_PROVIDER_CATALOG,
    EXTERNAL_RELATIONS_PRINCIPLES,
    EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE,
    EXTERNAL_RELATIONS_RECORD_KINDS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_157,
    INSTITUTIONAL_EXTERNAL_RELATIONS_FIX,
    INSTITUTIONAL_EXTERNAL_RELATIONS_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_157,
    SELF_DIRECTED_INSTITUTIONAL_DIPLOMACY_ENABLED_FIX_157,
    SOVEREIGNTY_DELEGATION_ENABLED_FIX_157,
    TRUST_CLASSIFICATIONS,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_service import (
    build_institutional_external_relations,
)
from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_store import (
    append_institutional_external_relations_record,
    clear_institutional_external_relations_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-external-cert-157"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_institutional_external_relations_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_institutional_external_relations_records_for_tests()


class TestMissionControlInstitutionalExternalRelationsCertification:
    def test_fix_157_contract(self) -> None:
        assert INSTITUTIONAL_EXTERNAL_RELATIONS_FIX == "FIX 157"
        assert INSTITUTIONAL_EXTERNAL_RELATIONS_SCHEMA_VERSION == (
            "mission_control_institutional_external_relations_v1"
        )
        assert MUTATION_PERFORMED_FIX_157 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157 is False
        assert AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157 is False
        assert AUTONOMOUS_PROVIDER_ALIGNMENT_ENABLED_FIX_157 is False
        assert SELF_DIRECTED_INSTITUTIONAL_DIPLOMACY_ENABLED_FIX_157 is False
        assert SOVEREIGNTY_DELEGATION_ENABLED_FIX_157 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_157 is False
        assert EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE is False
        assert "provider_relationship" in EXTERNAL_RELATIONS_RECORD_KINDS
        assert len(EXTERNAL_RELATIONS_PRINCIPLES) >= 8
        assert len(EXTERNAL_PROVIDER_CATALOG) >= 4
        assert len(TRUST_CLASSIFICATIONS) >= 4
        assert len(CONSTITUTIONAL_BOUNDARIES) >= 4

    def test_institutional_external_relations_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_institutional_external_relations_record(
            session_id=SESSION,
            kind="provider_relationship",
            content="Advisory: github provider under governed software delivery boundary.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_institutional_external_relations(session_id=SESSION)
        assert result.ok is True
        assert result.external_relations["constitutional_external_relations_cognition"] is True
        assert result.external_relations["external_relations_record_count"] == 1

    def test_operator_api_includes_institutional_external_relations_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/institutional-external-relations" in paths
        assert "/mission-control/institutional-external-relations/record" in paths
