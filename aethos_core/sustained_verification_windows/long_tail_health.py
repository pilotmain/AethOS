# SPDX-License-Identifier: Apache-2.0
"""Long tail health — sustained operational trust."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_stabilization.sustained_health import assess_sustained_health


def assess_long_tail_health() -> dict[str, Any]:
    return assess_sustained_health(hours_stable=3.0, threshold_hours=4.0)
