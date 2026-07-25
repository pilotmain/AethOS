# SPDX-License-Identifier: Apache-2.0
"""Sustained truth tracking — long-tail operational truth."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.runtime import assess_sustained_verification


def track_sustained_truth() -> dict[str, Any]:
    sustained = assess_sustained_verification()
    return {
        **sustained,
        "long_tail_active": sustained.get("extended_monitoring_active", True),
        "summary": "Long-tail operational truth tracking active across sustained verification.",
    }
