# SPDX-License-Identifier: Apache-2.0
"""Recovery survivability — recovery durability."""

from __future__ import annotations

from typing import Any

from aethos_core.degradation_acceleration.recovery_acceleration import measure_recovery_acceleration


def assess_recovery_survivability() -> dict[str, Any]:
    recovery = measure_recovery_acceleration()
    return {
        **recovery,
        "survivable": not recovery.get("accelerating", False),
        "summary": "Recovery survivability within durable bounds." if not recovery.get("accelerating") else "Recovery survivability monitoring active.",
    }
