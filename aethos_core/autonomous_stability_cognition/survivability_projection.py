# SPDX-License-Identifier: Apache-2.0
"""Survivability projection — long-tail forecasting."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_forecasting.survivability_projection import project_survivability


def project_autonomous_survivability(*, hours: float = 8.0) -> dict[str, Any]:
    return project_survivability(hours=hours)
