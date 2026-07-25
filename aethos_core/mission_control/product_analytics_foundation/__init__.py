# SPDX-License-Identifier: Apache-2.0
"""FIX 318 — product analytics and behavioral intelligence foundation."""

from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
    PRODUCT_ANALYTICS_FOUNDATION_DOMAINS,
    PRODUCT_ANALYTICS_FOUNDATION_FIX,
    PRODUCT_ANALYTICS_FOUNDATION_ROUTE_ID,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service import (
    build_product_analytics_foundation,
)

__all__ = [
    "PRODUCT_ANALYTICS_FOUNDATION_DOMAINS",
    "PRODUCT_ANALYTICS_FOUNDATION_FIX",
    "PRODUCT_ANALYTICS_FOUNDATION_ROUTE_ID",
    "build_product_analytics_foundation",
]
