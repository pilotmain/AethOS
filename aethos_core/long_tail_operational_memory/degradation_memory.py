# SPDX-License-Identifier: Apache-2.0
"""Degradation memory — instability history."""

from __future__ import annotations

from typing import Any

from aethos_core.infrastructure_intuition.degradation_signatures import detect_degradation_signatures


def recall_degradation_memory(*, pattern: str = "restart_loop") -> dict[str, Any]:
    return detect_degradation_signatures(pattern=pattern)
