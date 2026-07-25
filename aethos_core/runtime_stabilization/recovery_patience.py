# SPDX-License-Identifier: Apache-2.0
"""Recovery patience — operational stabilization pacing."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_stabilization.runtime_patience import assess_runtime_patience


def assess_recovery_patience(*, stabilization: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    patience = assess_runtime_patience(stabilization=stabilization, verification=verification)
    return {
        **patience,
        "recovery_patience_active": patience.get("premature_healthy_blocked", True),
        "summary": "Operational stabilization pacing active — recovery patience respected.",
    }
