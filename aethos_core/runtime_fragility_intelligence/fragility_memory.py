# SPDX-License-Identifier: Apache-2.0
"""Fragility memory — long-tail fragility history."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_fragility.fragility_memory import record_runtime_fragility_memory


def record_fragility_history(*, zone: str = "runtime_edge") -> dict[str, Any]:
    return record_runtime_fragility_memory(zone=zone)
