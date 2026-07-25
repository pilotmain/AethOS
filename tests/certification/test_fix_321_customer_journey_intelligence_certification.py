# SPDX-License-Identifier: Apache-2.0
"""FIX 321 — customer journey intelligence certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_321_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_contract import (
    CUSTOMER_JOURNEY_INTELLIGENCE_DOMAINS,
    CUSTOMER_JOURNEY_INTELLIGENCE_FIX,
    CUSTOMER_JOURNEY_INTELLIGENCE_ROUTE_ID,
)

pytestmark = pytest.mark.certification


class TestFix321CustomerJourneyIntelligenceCertification:
    def test_fix_321_contract(self) -> None:
        assert CUSTOMER_JOURNEY_INTELLIGENCE_FIX == "FIX 321"
        assert CUSTOMER_JOURNEY_INTELLIGENCE_ROUTE_ID == "mission_control_customer_journey_intelligence"
        assert len(CUSTOMER_JOURNEY_INTELLIGENCE_DOMAINS) == 10

    def test_fix_321_certification_requirement_count(self) -> None:
        assert len(FIX_321_CERTIFICATION_REQUIREMENTS) == 10
