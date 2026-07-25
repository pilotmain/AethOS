# SPDX-License-Identifier: Apache-2.0
"""Infrastructure journey — long-term operational patterns."""

from __future__ import annotations

from typing import Any

_JOURNEY: list[dict[str, Any]] = []


def record_journey_milestone(*, milestone: dict[str, Any]) -> None:
    _JOURNEY.append(milestone)
    if len(_JOURNEY) > 50:
        del _JOURNEY[:-50]


def infrastructure_journey_state() -> dict[str, Any]:
    return {"milestones": list(_JOURNEY[-10:]), "count": len(_JOURNEY)}
