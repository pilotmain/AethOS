# SPDX-License-Identifier: Apache-2.0
"""Operational endurance aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_endurance.endurance_runtime import orchestrate_operational_endurance


def assess_operational_endurance() -> dict[str, Any]:
    endurance = orchestrate_operational_endurance()
    return {"ok": True, **endurance}
