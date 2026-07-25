# SPDX-License-Identifier: Apache-2.0
"""Reconciliation memory — persistent reconciliation history."""

from __future__ import annotations

from typing import Any

_RECONCILIATION_MEMORY: list[dict[str, Any]] = []


def record_reconciliation(*, entry: dict[str, Any]) -> None:
    _RECONCILIATION_MEMORY.append(entry)
    if len(_RECONCILIATION_MEMORY) > 50:
        del _RECONCILIATION_MEMORY[:-50]


def reconciliation_memory_state() -> dict[str, Any]:
    return {"entries": list(_RECONCILIATION_MEMORY[-10:]), "count": len(_RECONCILIATION_MEMORY)}
