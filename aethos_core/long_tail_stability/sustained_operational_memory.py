# SPDX-License-Identifier: Apache-2.0
"""Sustained operational memory — long-term operational history."""

from __future__ import annotations

from typing import Any

from aethos_core.long_tail_operational_memory.runtime import assess_long_tail_operational_memory


def recall_sustained_operational_memory(*, provider: str = "railway") -> dict[str, Any]:
    return assess_long_tail_operational_memory(provider=provider)
