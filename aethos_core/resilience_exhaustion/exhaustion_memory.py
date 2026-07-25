# SPDX-License-Identifier: Apache-2.0
"""Exhaustion memory — exhaustion trajectory history."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_forecasting.forecasting_memory import record_forecasting_memory


def record_exhaustion_memory(*, stable: bool = True) -> dict[str, Any]:
    return record_forecasting_memory(survivable=stable)
