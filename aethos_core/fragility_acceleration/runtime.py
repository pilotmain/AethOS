# SPDX-License-Identifier: Apache-2.0
"""Fragility acceleration aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.fragility_acceleration.acceleration_runtime import orchestrate_fragility_acceleration


def assess_fragility_acceleration(*, provider: str = "railway") -> dict[str, Any]:
    acceleration = orchestrate_fragility_acceleration(provider=provider)
    return {"ok": True, **acceleration}
