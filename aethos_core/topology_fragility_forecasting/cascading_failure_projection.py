# SPDX-License-Identifier: Apache-2.0
"""Cascading failure projection — propagation forecasting."""

from __future__ import annotations

from typing import Any

from aethos_core.topology_stability_forecasting.cascading_failure_forecasting import forecast_cascading_failure


def project_cascading_failure() -> dict[str, Any]:
    return forecast_cascading_failure()
