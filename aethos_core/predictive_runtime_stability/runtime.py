# SPDX-License-Identifier: Apache-2.0
"""Predictive runtime stability aggregate."""

from __future__ import annotations

from typing import Any

from aethos_core.predictive_runtime_stability.predictive_runtime import orchestrate_predictive_stability


def assess_predictive_runtime_stability() -> dict[str, Any]:
    stability = orchestrate_predictive_stability()
    return {"ok": True, **stability}
