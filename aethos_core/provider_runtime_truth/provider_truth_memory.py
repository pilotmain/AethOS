# SPDX-License-Identifier: Apache-2.0
"""Provider truth memory — provider convergence history."""

from __future__ import annotations

from typing import Any

_LOG: list[dict[str, Any]] = []


def record_provider_convergence(*, provider: str, converged: bool) -> dict[str, Any]:
    entry = {"provider": provider, "converged": converged}
    _LOG.append(entry)
    if len(_LOG) > 100:
        del _LOG[:-100]
    return {"provider_history_count": len(_LOG), "latest": entry}
