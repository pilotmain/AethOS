# SPDX-License-Identifier: Apache-2.0
"""Cascading endurance projection — propagation survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_fragility_forecasting.cascading_failure_projection import project_cascading_failure


def project_cascading_endurance() -> dict[str, Any]:
    cascading = project_cascading_failure()
    return {
        **cascading,
        "enduring": cascading.get("protected", True),
        "summary": "Cascading endurance within durable bounds.",
    }
