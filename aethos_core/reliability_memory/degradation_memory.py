# SPDX-License-Identifier: Apache-2.0
"""Degradation memory — recurring failure pathways."""

from __future__ import annotations

from typing import Any

_DEGRADATION_MEMORY: list[dict[str, Any]] = []


def record_degradation_pathway(*, pathway: str, service: str) -> None:
    _DEGRADATION_MEMORY.append({"pathway": pathway, "service": service})
    if len(_DEGRADATION_MEMORY) > 100:
        del _DEGRADATION_MEMORY[:-100]


def degradation_memory_state() -> dict[str, Any]:
    return {"pathways": list(_DEGRADATION_MEMORY[-15:]), "count": len(_DEGRADATION_MEMORY)}
