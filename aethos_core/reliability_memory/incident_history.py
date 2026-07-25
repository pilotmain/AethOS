# SPDX-License-Identifier: Apache-2.0
"""Incident history — recurring operational issues."""

from __future__ import annotations

from typing import Any

_INCIDENT_HISTORY: list[dict[str, Any]] = []


def record_incident(*, entry: dict[str, Any]) -> None:
    _INCIDENT_HISTORY.append(entry)
    if len(_INCIDENT_HISTORY) > 200:
        del _INCIDENT_HISTORY[:-200]


def incident_history_state() -> dict[str, Any]:
    return {"incidents": list(_INCIDENT_HISTORY[-20:]), "count": len(_INCIDENT_HISTORY)}
