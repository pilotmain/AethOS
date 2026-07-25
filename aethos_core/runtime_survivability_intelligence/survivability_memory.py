# SPDX-License-Identifier: Apache-2.0
"""Survivability memory — long-tail survivability history."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_fragility_intelligence.fragility_memory import record_fragility_history


def record_survivability_memory() -> dict[str, Any]:
    return record_fragility_history()
