# SPDX-License-Identifier: Apache-2.0
"""Stability memory — long-tail operational history."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_stability_forecasting.stability_memory import record_stability_memory


def record_predictive_stability_memory(*, stable: bool = True) -> dict[str, Any]:
    return record_stability_memory(stable=stable)
