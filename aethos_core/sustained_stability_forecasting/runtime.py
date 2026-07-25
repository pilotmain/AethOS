# SPDX-License-Identifier: Apache-2.0
"""Sustained stability forecasting aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_stability_forecasting.stability_forecasting_runtime import orchestrate_stability_forecasting


def assess_sustained_stability_forecasting() -> dict[str, Any]:
    forecast = orchestrate_stability_forecasting()
    return {"ok": True, **forecast}
