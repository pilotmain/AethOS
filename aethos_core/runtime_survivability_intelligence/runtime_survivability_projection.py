# SPDX-License-Identifier: Apache-2.0
"""Runtime survivability projection — long-tail survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.predictive_runtime_stability.long_tail_projection import project_future_stability


def project_runtime_survivability() -> dict[str, Any]:
    stability = project_future_stability()
    return {
        **stability,
        "survivable": stability.get("projection_stable", True),
        "summary": "Long-tail runtime survivability within durable bounds.",
    }
