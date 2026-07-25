# SPDX-License-Identifier: Apache-2.0
"""Resilience patterns — long-tail stability."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_resilience_memory.resilience_pattern_memory import recall_resilience_patterns


def recall_resilience_patterns_long_tail(*, pattern: str = "sustained_durability") -> dict[str, Any]:
    return recall_resilience_patterns(pattern=pattern)
