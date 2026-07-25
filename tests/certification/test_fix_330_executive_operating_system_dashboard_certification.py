# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_330_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_FIX,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID,
)

pytestmark = pytest.mark.certification


class TestFix330ExecutiveOperatingSystemDashboardCertification:
    def test_fix_330_contract(self) -> None:
        assert EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_FIX == "FIX 330"
        assert (
            EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID
            == "mission_control_executive_operating_system_dashboard"
        )
        assert len(EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS) == 10

    def test_fix_330_certification_requirement_count(self) -> None:
        assert len(FIX_330_CERTIFICATION_REQUIREMENTS) == 10
