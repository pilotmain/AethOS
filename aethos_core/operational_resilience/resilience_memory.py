# SPDX-License-Identifier: Apache-2.0
"""Resilience memory — operational resilience history."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_resilience_cognition.sustained_resilience_memory import record_sustained_resilience


def record_resilience_memory(*, resilient: bool) -> dict[str, Any]:
    return record_sustained_resilience(resilient=resilient)
