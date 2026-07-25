# SPDX-License-Identifier: Apache-2.0
"""Degradation acceleration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.degradation_acceleration.acceleration_runtime import orchestrate_degradation_acceleration


def assess_degradation_acceleration(*, provider: str = "railway") -> dict[str, Any]:
    acceleration = orchestrate_degradation_acceleration(provider=provider)
    return {"ok": True, **acceleration}
