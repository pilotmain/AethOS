# SPDX-License-Identifier: Apache-2.0
"""Stability memory — long-tail operational history."""

from __future__ import annotations

from typing import Any

from aethos_core.predictive_operational_cognition.predictive_memory import record_predictive_memory


def record_stability_memory(*, stable: bool = True) -> dict[str, Any]:
    return record_predictive_memory(stable=stable)
