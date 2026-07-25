# SPDX-License-Identifier: Apache-2.0
"""Restart loop decay — restart instability."""

from __future__ import annotations

from typing import Any


def assess_restart_loop_decay(*, restart_count: int = 2, threshold: int = 5) -> dict[str, Any]:
    unstable = restart_count >= threshold
    return {
        "restart_count": restart_count,
        "restart_loop_detected": unstable,
        "summary": "Restart loop instability detected." if unstable else "Restart stability within monitoring window.",
    }
