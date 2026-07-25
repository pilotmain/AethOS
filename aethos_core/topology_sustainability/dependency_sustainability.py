# SPDX-License-Identifier: Apache-2.0
"""Dependency sustainability — downstream survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_survivability.dependency_survivability import assess_dependency_survivability


def assess_dependency_sustainability() -> dict[str, Any]:
    return assess_dependency_survivability()
