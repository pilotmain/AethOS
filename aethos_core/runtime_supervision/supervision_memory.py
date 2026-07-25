# SPDX-License-Identifier: Apache-2.0
"""Supervision memory — recurring runtime failures."""

from __future__ import annotations

from typing import Any

_SUPERVISION_MEMORY: list[dict[str, Any]] = []


def record_supervision_event(*, event: dict[str, Any]) -> None:
    _SUPERVISION_MEMORY.append(event)
    if len(_SUPERVISION_MEMORY) > 100:
        del _SUPERVISION_MEMORY[:-100]


def supervision_memory_state() -> dict[str, Any]:
    return {"events": list(_SUPERVISION_MEMORY[-20:]), "count": len(_SUPERVISION_MEMORY)}
