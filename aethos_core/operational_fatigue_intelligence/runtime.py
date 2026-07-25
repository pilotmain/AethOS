# SPDX-License-Identifier: Apache-2.0
"""Operational fatigue intelligence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_intelligence.fatigue_runtime import orchestrate_operational_fatigue


def assess_operational_fatigue_intelligence() -> dict[str, Any]:
    fatigue = orchestrate_operational_fatigue()
    return {"ok": True, **fatigue}
