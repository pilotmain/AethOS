# SPDX-License-Identifier: Apache-2.0
"""Runtime truth memory — convergence history."""

from __future__ import annotations

from typing import Any

_HISTORY: list[dict[str, Any]] = []


def record_truth_convergence(*, converged: bool, tier: str) -> dict[str, Any]:
    entry = {"converged": converged, "tier": tier}
    _HISTORY.append(entry)
    if len(_HISTORY) > 100:
        del _HISTORY[:-100]
    return {"history_count": len(_HISTORY), "latest": entry}
