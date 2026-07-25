# SPDX-License-Identifier: Apache-2.0
"""Dependency pressure — downstream recovery pressure."""

from __future__ import annotations

from typing import Any


def assess_dependency_pressure(*, pressure_score: float = 0.35) -> dict[str, Any]:
    return {
        "pressure_score": pressure_score,
        "pressure_bounded": pressure_score < 0.7,
        "summary": "Dependency recovery pressure within acceptable bounds."
        if pressure_score < 0.7
        else "Elevated dependency recovery pressure detected.",
    }
