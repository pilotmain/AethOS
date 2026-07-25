# SPDX-License-Identifier: Apache-2.0
"""Recovery acceleration — recovery fragility escalation."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_fragility.recovery_fragility import assess_recovery_fragility


def measure_recovery_acceleration() -> dict[str, Any]:
    recovery = assess_recovery_fragility()
    return {
        **recovery,
        "accelerating": recovery.get("unstable", False),
        "summary": "Recovery fragility escalation bounded." if not recovery.get("unstable") else "Recovery asymmetry escalation emerging.",
    }
