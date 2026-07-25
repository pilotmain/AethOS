# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — growth & adoption intelligence."""

from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_contract import (
    GROWTH_ADOPTION_INTELLIGENCE_DOMAINS,
    GROWTH_ADOPTION_INTELLIGENCE_FIX,
    GROWTH_ADOPTION_INTELLIGENCE_ROUTE_ID,
)
from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_service import (
    build_growth_adoption_intelligence,
)

__all__ = [
    "GROWTH_ADOPTION_INTELLIGENCE_DOMAINS",
    "GROWTH_ADOPTION_INTELLIGENCE_FIX",
    "GROWTH_ADOPTION_INTELLIGENCE_ROUTE_ID",
    "build_growth_adoption_intelligence",
]
