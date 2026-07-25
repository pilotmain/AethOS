# SPDX-License-Identifier: Apache-2.0
"""Drift repair detection — reconciliation awareness."""

from __future__ import annotations

from typing import Any


def detect_drift_repair(*, state_diff: dict[str, Any], drift: dict[str, Any]) -> dict[str, Any]:
    repair_needed = bool(state_diff.get("missing") or state_diff.get("extra") or drift.get("drift_detected"))
    return {
        "repair_needed": repair_needed,
        "reconciliation_alert": repair_needed,
        "summary": "Reconciliation repair recommended." if repair_needed else "No drift repair required.",
    }
