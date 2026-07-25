# SPDX-License-Identifier: Apache-2.0
"""FIX 324 — strategic portfolio intelligence certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_324_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_contract import (
    STRATEGIC_PORTFOLIO_INTELLIGENCE_DOMAINS,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_FIX,
    STRATEGIC_PORTFOLIO_INTELLIGENCE_ROUTE_ID,
)

pytestmark = pytest.mark.certification


class TestFix324StrategicPortfolioIntelligenceCertification:
    def test_fix_324_contract(self) -> None:
        assert STRATEGIC_PORTFOLIO_INTELLIGENCE_FIX == "FIX 324"
        assert STRATEGIC_PORTFOLIO_INTELLIGENCE_ROUTE_ID == "mission_control_strategic_portfolio_intelligence"
        assert len(STRATEGIC_PORTFOLIO_INTELLIGENCE_DOMAINS) == 10

    def test_fix_324_certification_requirement_count(self) -> None:
        assert len(FIX_324_CERTIFICATION_REQUIREMENTS) == 10
