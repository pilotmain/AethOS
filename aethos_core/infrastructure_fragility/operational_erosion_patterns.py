# SPDX-License-Identifier: Apache-2.0
"""Operational erosion patterns — gradual instability."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_intuition.degradation_signatures import detect_degradation_signatures


def detect_operational_erosion_patterns(*, pattern: str = "gradual_drift") -> dict[str, Any]:
    return detect_degradation_signatures(pattern=pattern)
