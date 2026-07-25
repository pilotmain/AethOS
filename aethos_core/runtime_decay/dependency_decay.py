# SPDX-License-Identifier: Apache-2.0
"""Dependency decay — downstream instability."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_stabilization.dependency_pressure import assess_dependency_pressure


def assess_dependency_decay() -> dict[str, Any]:
    pressure = assess_dependency_pressure()
    return {
        **pressure,
        "downstream_unstable": not pressure.get("pressure_bounded", True),
        "summary": "Downstream dependency instability detected." if not pressure.get("pressure_bounded") else "Downstream dependencies stable.",
    }
