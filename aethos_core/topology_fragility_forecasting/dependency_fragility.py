# SPDX-License-Identifier: Apache-2.0
"""Dependency fragility — downstream collapse forecasting."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_stability_forecasting.dependency_projection import project_dependency_collapse


def forecast_dependency_fragility() -> dict[str, Any]:
    return project_dependency_collapse()
