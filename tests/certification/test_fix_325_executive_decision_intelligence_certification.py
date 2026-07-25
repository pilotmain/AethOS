# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_325_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
    EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS,
    EXECUTIVE_DECISION_INTELLIGENCE_FIX,
    EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID,
)

pytestmark = pytest.mark.certification


class TestFix325ExecutiveDecisionIntelligenceCertification:
    def test_fix_325_contract(self) -> None:
        assert EXECUTIVE_DECISION_INTELLIGENCE_FIX == "FIX 325"
        assert EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID == "mission_control_executive_decision_intelligence"
        assert len(EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS) == 10

    def test_fix_325_certification_requirement_count(self) -> None:
        assert len(FIX_325_CERTIFICATION_REQUIREMENTS) == 10
