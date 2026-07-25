# SPDX-License-Identifier: Apache-2.0
"""Rollback decay — post-rollback degradation."""

from __future__ import annotations

from typing import Any


def assess_rollback_decay(*, stable: bool = True) -> dict[str, Any]:
    return {
        "post_rollback_stable": stable,
        "decay_detected": not stable,
        "summary": "Post-rollback stability maintained." if stable else "Post-rollback degradation detected.",
    }
