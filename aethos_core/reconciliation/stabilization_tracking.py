# SPDX-License-Identifier: Apache-2.0
"""Stabilization tracking — recovery lifecycle."""

from __future__ import annotations

from typing import Any


def track_stabilization(*, verification: dict[str, Any], state_diff: dict[str, Any]) -> dict[str, Any]:
    if verification.get("verified") and state_diff.get("aligned"):
        phase = "stabilized"
    elif verification.get("verified"):
        phase = "stabilizing"
    elif state_diff.get("drift_detected"):
        phase = "failed"
    else:
        phase = "monitoring"
    return {
        "stabilization_phase": phase,
        "stabilization_complete": phase == "stabilized",
        "extended_monitoring_active": True,
    }
