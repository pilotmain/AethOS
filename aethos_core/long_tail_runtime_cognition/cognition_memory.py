# SPDX-License-Identifier: Apache-2.0
"""Cognition memory — operational trajectory history."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_survivability_intelligence.survivability_memory import record_survivability_memory


def record_cognition_memory() -> dict[str, Any]:
    return record_survivability_memory()
