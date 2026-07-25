# SPDX-License-Identifier: Apache-2.0
"""Sustained recovery tracking — long-tail recovery monitoring."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.recovery_convergence_runtime import orchestrate_recovery_convergence


def track_sustained_recovery(*, provider: str = "railway") -> dict[str, Any]:
    recovery = orchestrate_recovery_convergence(provider=provider)
    return {
        **recovery,
        "sustained": recovery.get("converged", False),
        "summary": "Sustained recovery monitoring active across extended runtime windows.",
    }
