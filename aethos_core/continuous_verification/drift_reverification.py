# SPDX-License-Identifier: Apache-2.0
"""Drift reverification — post-recovery validation."""

from __future__ import annotations

from typing import Any


def reverify_after_recovery(*, reconciliation: dict[str, Any]) -> dict[str, Any]:
    drift = reconciliation.get("drift_repair") or {}
    state_diff = reconciliation.get("state_diff") or {}
    aligned = state_diff.get("aligned", False) and not drift.get("repair_needed", True)
    return {
        "reverified": aligned,
        "drift_repair_needed": drift.get("repair_needed", False),
        "summary": "Post-recovery drift reverification passed." if aligned else "Post-recovery drift reverification incomplete.",
    }
