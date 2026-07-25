# SPDX-License-Identifier: Apache-2.0
"""Stabilization regression — post-recovery decay."""

from __future__ import annotations

from typing import Any

from aethos_core.rollback_integrity.rollback_decay import assess_rollback_decay


def assess_stabilization_regression(*, stable: bool = True) -> dict[str, Any]:
    decay = assess_rollback_decay(stable=stable)
    return {
        **decay,
        "regression_detected": not decay.get("post_rollback_stable", True),
        "summary": "Post-recovery stabilization regression detected." if not decay.get("post_rollback_stable") else "No stabilization regression detected.",
    }
