# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard."""

from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_FIX,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_service import (
    build_executive_operating_system_dashboard_board,
)

__all__ = [
    "EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS",
    "EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_FIX",
    "EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID",
    "build_executive_operating_system_dashboard_board",
]
