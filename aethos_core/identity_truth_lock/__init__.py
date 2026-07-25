# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — creator attribution and platform identity truth lock."""

from aethos_core.identity_truth_lock.identity_truth_lock_contract import (
    IDENTITY_TRUTH_LOCK_DOMAINS,
    IDENTITY_TRUTH_LOCK_FIX,
    IDENTITY_TRUTH_LOCK_ROUTE_ID,
)
from aethos_core.identity_truth_lock.identity_truth_lock_service import build_identity_truth_lock

__all__ = [
    "IDENTITY_TRUTH_LOCK_DOMAINS",
    "IDENTITY_TRUTH_LOCK_FIX",
    "IDENTITY_TRUTH_LOCK_ROUTE_ID",
    "build_identity_truth_lock",
]
