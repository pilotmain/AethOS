# SPDX-License-Identifier: Apache-2.0
"""Recovery tracking — stabilization lifecycle."""

from __future__ import annotations

from typing import Any


def track_recovery(*, verification: dict[str, Any], stabilization: dict[str, Any]) -> dict[str, Any]:
    phase = stabilization.get("stabilization_phase") or "monitoring"
    return {
        "recovery_phase": phase,
        "stabilization_complete": stabilization.get("stabilization_complete", False),
        "extended_monitoring_active": stabilization.get("extended_monitoring_active", True),
        "verified": verification.get("verified", False),
    }
