# SPDX-License-Identifier: Apache-2.0
"""Recovery durability projection — recovery persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.degradation_acceleration.recovery_acceleration import measure_recovery_acceleration


def project_recovery_durability() -> dict[str, Any]:
    recovery = measure_recovery_acceleration()
    return {
        **recovery,
        "durable": not recovery.get("accelerating", False),
        "summary": "Recovery durability persistence within durable bounds.",
    }
