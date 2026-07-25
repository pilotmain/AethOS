# SPDX-License-Identifier: Apache-2.0
"""Runtime fragility aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_fragility.fragility_runtime import orchestrate_runtime_fragility


def assess_runtime_fragility(*, provider: str = "railway") -> dict[str, Any]:
    fragility = orchestrate_runtime_fragility(provider=provider)
    return {"ok": True, **fragility}
