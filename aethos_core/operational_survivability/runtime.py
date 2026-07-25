# SPDX-License-Identifier: Apache-2.0
"""Operational survivability aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_survivability.survivability_runtime import orchestrate_operational_survivability


def assess_operational_survivability() -> dict[str, Any]:
    survivability = orchestrate_operational_survivability()
    return {"ok": True, **survivability}
