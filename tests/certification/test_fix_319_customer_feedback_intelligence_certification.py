# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — customer feedback intelligence certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_319_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_contract import (
    CUSTOMER_FEEDBACK_INTELLIGENCE_DOMAINS,
    CUSTOMER_FEEDBACK_INTELLIGENCE_FIX,
    CUSTOMER_FEEDBACK_INTELLIGENCE_ROUTE_ID,
)

pytestmark = pytest.mark.certification


class TestFix319CustomerFeedbackIntelligenceCertification:
    def test_fix_319_contract(self) -> None:
        assert CUSTOMER_FEEDBACK_INTELLIGENCE_FIX == "FIX 319"
        assert CUSTOMER_FEEDBACK_INTELLIGENCE_ROUTE_ID == "mission_control_customer_feedback_intelligence"
        assert len(CUSTOMER_FEEDBACK_INTELLIGENCE_DOMAINS) == 10

    def test_fix_319_certification_requirement_count(self) -> None:
        assert len(FIX_319_CERTIFICATION_REQUIREMENTS) == 10
