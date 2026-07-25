# SPDX-License-Identifier: Apache-2.0
"""FIX 151 — governance doctrine certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_doctrine.governance_doctrine_contract import (
    AMENDMENT_PROPOSAL_EXECUTABLE,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151,
    AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151,
    DOCTRINE_RECORD_KINDS,
    GOVERNANCE_DOCTRINE_FIX,
    GOVERNANCE_DOCTRINE_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_151,
    GOVERNANCE_PRINCIPLES,
    MUTATION_PERFORMED_FIX_151,
    SELF_MODIFYING_GOVERNANCE_ENABLED_FIX_151,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_service import build_governance_doctrine
from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import (
    append_governance_doctrine_record,
    clear_governance_doctrine_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-doctrine-cert-151"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_doctrine_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_doctrine_records_for_tests()


class TestMissionControlGovernanceDoctrineCertification:
    def test_fix_151_contract(self) -> None:
        assert GOVERNANCE_DOCTRINE_FIX == "FIX 151"
        assert GOVERNANCE_DOCTRINE_SCHEMA_VERSION == "mission_control_governance_doctrine_v1"
        assert MUTATION_PERFORMED_FIX_151 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151 is False
        assert AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151 is False
        assert SELF_MODIFYING_GOVERNANCE_ENABLED_FIX_151 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_151 is False
        assert AMENDMENT_PROPOSAL_EXECUTABLE is False
        assert "policy_amendment_proposal" in DOCTRINE_RECORD_KINDS
        assert len(GOVERNANCE_PRINCIPLES) >= 7

    def test_governance_doctrine_constitutionality_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_governance_doctrine_record(
            session_id=SESSION,
            kind="policy_amendment_proposal",
            content="Advisory-only amendment: document hold precedent for multi-gate missions.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_governance_doctrine(session_id=SESSION)
        assert result.ok is True
        assert result.doctrine["institutional_governance_constitutionality"] is True
        assert len(result.doctrine["sections"]["policy_amendment_proposals"]) == 1

    def test_operator_api_includes_governance_doctrine_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-doctrine" in paths
        assert "/mission-control/governance-doctrine/record" in paths
