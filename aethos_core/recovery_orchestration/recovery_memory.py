# SPDX-License-Identifier: Apache-2.0
"""Recovery memory — recurring recovery patterns."""

from __future__ import annotations

from typing import Any

_RECOVERY_MEMORY: list[dict[str, Any]] = []


def record_recovery_pattern(*, entry: dict[str, Any]) -> None:
    _RECOVERY_MEMORY.append(entry)
    if len(_RECOVERY_MEMORY) > 100:
        del _RECOVERY_MEMORY[:-100]


def recovery_memory_state() -> dict[str, Any]:
    return {"patterns": list(_RECOVERY_MEMORY[-15:]), "count": len(_RECOVERY_MEMORY)}
