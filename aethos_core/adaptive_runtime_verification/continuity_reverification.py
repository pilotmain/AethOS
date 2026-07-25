# SPDX-License-Identifier: Apache-2.0
"""Continuity reverification — long-tail rechecks."""

from __future__ import annotations

from typing import Any

from aethos_core.recovery_convergence.recovery_convergence_runtime import orchestrate_recovery_convergence


def run_continuity_reverification(*, provider: str = "railway") -> dict[str, Any]:
    recovery = orchestrate_recovery_convergence(provider=provider)
    return {
        **recovery,
        "reverified": recovery.get("converged", False),
        "summary": "Long-tail continuity reverification active.",
    }
