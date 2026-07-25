# SPDX-License-Identifier: Apache-2.0
"""Survivability memory — survivability history."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_resilience.resilience_journey_memory import recall_operational_evolution


def record_survivability_memory() -> dict[str, Any]:
    return recall_operational_evolution()
