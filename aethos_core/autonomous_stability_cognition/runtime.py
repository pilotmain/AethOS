# SPDX-License-Identifier: Apache-2.0
"""Autonomous stability cognition aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.autonomous_stability_cognition.cognition_runtime import orchestrate_autonomous_stability


def assess_autonomous_stability_cognition(*, provider: str = "railway") -> dict[str, Any]:
    cognition = orchestrate_autonomous_stability(provider=provider)
    return {"ok": True, **cognition}
