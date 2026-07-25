# SPDX-License-Identifier: Apache-2.0
"""Dependency decay tracking — downstream degradation."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_decay.dependency_decay import assess_dependency_decay


def track_dependency_decay() -> dict[str, Any]:
    return assess_dependency_decay()
