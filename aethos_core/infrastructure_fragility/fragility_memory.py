# SPDX-License-Identifier: Apache-2.0
"""Fragility memory — long-tail fragility history."""

from __future__ import annotations

from typing import Any

_FRAGILITY_LOG: list[str] = []


def record_fragility_memory(*, zone: str) -> dict[str, Any]:
    _FRAGILITY_LOG.append(zone)
    if len(_FRAGILITY_LOG) > 30:
        del _FRAGILITY_LOG[:-30]
    return {"fragility_zones_tracked": len(_FRAGILITY_LOG), "latest_zone": zone}
