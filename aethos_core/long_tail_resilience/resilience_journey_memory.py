# SPDX-License-Identifier: Apache-2.0
"""Resilience journey memory — operational evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_resilience_memory.resilience_journey_memory import recall_resilience_journey


def recall_operational_evolution() -> dict[str, Any]:
    journey = recall_resilience_journey()
    return {**journey, "journey_stage": "runtime_resilience_cognition"}
