# SPDX-License-Identifier: Apache-2.0
"""FIX 152 — governance policy interpretation certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_contract import (
    AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152,
    AUTONOMOUS_GOVERNANCE_RULINGS_ENABLED_FIX_152,
    GOVERNANCE_MUTATION_PERFORMED_FIX_152,
    GOVERNANCE_POLICY_INTERPRETATION_FIX,
    GOVERNANCE_POLICY_INTERPRETATION_SCHEMA_VERSION,
    INTERPRETATION_ASSISTANCE_PRINCIPLES,
    INTERPRETATION_EXECUTABLE,
    INTERPRETATION_RECORD_KINDS,
    MUTATION_PERFORMED_FIX_152,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_service import (
    build_governance_policy_interpretation,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
    append_governance_policy_interpretation_record,
    clear_governance_policy_interpretation_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-interpretation-cert-152"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_policy_interpretation_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_policy_interpretation_records_for_tests()


class TestMissionControlGovernancePolicyInterpretationCertification:
    def test_fix_152_contract(self) -> None:
        assert GOVERNANCE_POLICY_INTERPRETATION_FIX == "FIX 152"
        assert GOVERNANCE_POLICY_INTERPRETATION_SCHEMA_VERSION == (
            "mission_control_governance_policy_interpretation_v1"
        )
        assert MUTATION_PERFORMED_FIX_152 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152 is False
        assert AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152 is False
        assert AUTONOMOUS_GOVERNANCE_RULINGS_ENABLED_FIX_152 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_152 is False
        assert INTERPRETATION_EXECUTABLE is False
        assert "doctrine_interpretation" in INTERPRETATION_RECORD_KINDS
        assert len(INTERPRETATION_ASSISTANCE_PRINCIPLES) >= 8

    def test_governance_policy_interpretation_reasoning_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_governance_policy_interpretation_record(
            session_id=SESSION,
            kind="doctrine_interpretation",
            content="Advisory reading: quorum composition is deliberation guidance, not execution authority.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_governance_policy_interpretation(session_id=SESSION)
        assert result.ok is True
        assert result.interpretation["institutional_constitutional_reasoning"] is True
        assert len(result.interpretation["sections"]["doctrine_interpretation_records"]) == 1

    def test_operator_api_includes_governance_policy_interpretation_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-policy-interpretation" in paths
        assert "/mission-control/governance-policy-interpretation/record" in paths
