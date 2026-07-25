# SPDX-License-Identifier: Apache-2.0
"""Adaptive runtime verification aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.adaptive_runtime_verification.adaptive_runtime import orchestrate_adaptive_runtime


def assess_adaptive_runtime_verification(*, provider: str = "railway") -> dict[str, Any]:
    adaptive = orchestrate_adaptive_runtime(provider=provider)
    return {"ok": True, **adaptive}
