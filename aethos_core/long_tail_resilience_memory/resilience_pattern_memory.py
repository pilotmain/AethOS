# SPDX-License-Identifier: Apache-2.0
"""Resilience pattern memory — stability history."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_intuition.operational_pattern_memory import remember_operational_pattern


def recall_resilience_patterns(*, pattern: str = "sustained_resilience") -> dict[str, Any]:
    return remember_operational_pattern(pattern=pattern)
