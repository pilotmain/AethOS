# SPDX-License-Identifier: Apache-2.0
"""FIX 326 — strategic planning intelligence certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_326_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_contract import (
    STRATEGIC_PLANNING_INTELLIGENCE_DOMAINS,
    STRATEGIC_PLANNING_INTELLIGENCE_FIX,
    STRATEGIC_PLANNING_INTELLIGENCE_ROUTE_ID,
)

pytestmark = pytest.mark.certification


class TestFix326StrategicPlanningIntelligenceCertification:
    def test_fix_326_contract(self) -> None:
        assert STRATEGIC_PLANNING_INTELLIGENCE_FIX == "FIX 326"
        assert STRATEGIC_PLANNING_INTELLIGENCE_ROUTE_ID == "mission_control_strategic_planning_intelligence"
        assert len(STRATEGIC_PLANNING_INTELLIGENCE_DOMAINS) == 10

    def test_fix_326_certification_requirement_count(self) -> None:
        assert len(FIX_326_CERTIFICATION_REQUIREMENTS) == 10
