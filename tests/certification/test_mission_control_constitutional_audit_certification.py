# SPDX-License-Identifier: Apache-2.0
"""FIX 160 — constitutional audit certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.constitutional_audit.constitutional_audit_contract import (
    ACCOUNTABILITY_PRINCIPLES,
    AUDIT_RECOMMENDATION_EXECUTABLE,
    AUDIT_RECORD_KINDS,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160,
    AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160,
    CONSTITUTIONAL_AUDIT_FIX,
    CONSTITUTIONAL_AUDIT_SCHEMA_VERSION,
    CONSTITUTIONAL_LAYER_LINKAGE,
    DISCLOSURE_BOUNDARIES,
    GOVERNANCE_ENFORCEMENT_ENABLED_FIX_160,
    GOVERNANCE_MUTATION_PERFORMED_FIX_160,
    MUTATION_PERFORMED_FIX_160,
    PUBLIC_COMMUNICATION_AUTHORITY_ENABLED_FIX_160,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_service import (
    build_constitutional_audit,
)
from aethos_core.mission_control.constitutional_audit.constitutional_audit_store import (
    append_constitutional_audit_record,
    clear_constitutional_audit_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-audit-cert-160"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_audit_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_constitutional_audit_records_for_tests()


class TestMissionControlConstitutionalAuditCertification:
    def test_fix_160_contract(self) -> None:
        assert CONSTITUTIONAL_AUDIT_FIX == "FIX 160"
        assert CONSTITUTIONAL_AUDIT_SCHEMA_VERSION == "mission_control_constitutional_audit_v1"
        assert MUTATION_PERFORMED_FIX_160 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160 is False
        assert AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160 is False
        assert PUBLIC_COMMUNICATION_AUTHORITY_ENABLED_FIX_160 is False
        assert GOVERNANCE_ENFORCEMENT_ENABLED_FIX_160 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_160 is False
        assert AUDIT_RECOMMENDATION_EXECUTABLE is False
        assert "audit_report" in AUDIT_RECORD_KINDS
        assert len(ACCOUNTABILITY_PRINCIPLES) >= 8
        assert len(CONSTITUTIONAL_LAYER_LINKAGE) >= 10
        assert len(DISCLOSURE_BOUNDARIES) >= 4

    def test_constitutional_audit_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_constitutional_audit_record(
            session_id=SESSION,
            kind="audit_report",
            content="Advisory: full constitutional stack audit for internal human governance review.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_constitutional_audit(session_id=SESSION)
        assert result.ok is True
        assert result.constitutional_audit["constitutional_accountability_cognition"] is True
        assert result.constitutional_audit["audit_record_count"] == 1

    def test_operator_api_includes_constitutional_audit_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/constitutional-audit" in paths
        assert "/mission-control/constitutional-audit/record" in paths
