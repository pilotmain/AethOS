# SPDX-License-Identifier: Apache-2.0
"""Temporal trust memory — historical trust evolution."""

from __future__ import annotations

from typing import Any

_TRUST_LOG: list[float] = []


def record_trust_evolution(*, score: float) -> dict[str, Any]:
    _TRUST_LOG.append(score)
    if len(_TRUST_LOG) > 50:
        del _TRUST_LOG[:-50]
    return {"trust_history_count": len(_TRUST_LOG), "latest_score": score}
