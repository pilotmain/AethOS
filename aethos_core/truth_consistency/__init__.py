# SPDX-License-Identifier: Apache-2.0
"""FIX 316C — truth consistency and hallucination prevention."""

from aethos_core.truth_consistency.truth_consistency_contract import (
    TRUTH_CONSISTENCY_DOMAINS,
    TRUTH_CONSISTENCY_FIX,
    TRUTH_CONSISTENCY_ROUTE_ID,
)
from aethos_core.truth_consistency.truth_consistency_service import build_truth_consistency

__all__ = [
    "TRUTH_CONSISTENCY_DOMAINS",
    "TRUTH_CONSISTENCY_FIX",
    "TRUTH_CONSISTENCY_ROUTE_ID",
    "build_truth_consistency",
]
