# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence."""

from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
    EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS,
    EXECUTIVE_DECISION_INTELLIGENCE_FIX,
    EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_service import (
    build_executive_decision_intelligence,
)

__all__ = [
    "EXECUTIVE_DECISION_INTELLIGENCE_DOMAINS",
    "EXECUTIVE_DECISION_INTELLIGENCE_FIX",
    "EXECUTIVE_DECISION_INTELLIGENCE_ROUTE_ID",
    "build_executive_decision_intelligence",
]
