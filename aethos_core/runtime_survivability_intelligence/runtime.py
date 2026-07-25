# SPDX-License-Identifier: Apache-2.0
"""Runtime survivability intelligence aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_survivability_intelligence.survivability_runtime import orchestrate_runtime_survivability


def assess_runtime_survivability_intelligence(*, provider: str = "railway") -> dict[str, Any]:
    survivability = orchestrate_runtime_survivability(provider=provider)
    return {"ok": True, **survivability}
