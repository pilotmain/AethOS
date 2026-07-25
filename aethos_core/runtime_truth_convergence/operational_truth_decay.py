# SPDX-License-Identifier: Apache-2.0
"""Operational truth decay — truth erosion detection."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_decay.runtime import assess_long_tail_operational_decay


def detect_operational_truth_decay() -> dict[str, Any]:
    decay = assess_long_tail_operational_decay()
    return {
        **decay,
        "truth_erosion_bounded": decay.get("decay_bounded", True),
        "summary": decay.get("summary", "Operational truth decay monitoring active."),
    }
