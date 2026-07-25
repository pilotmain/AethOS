# SPDX-License-Identifier: Apache-2.0
"""Fragility decay — degradation-aware trust."""

from __future__ import annotations

from typing import Any

from aethos_core.temporal_trust_evolution.fragility_confidence_decay import assess_fragility_confidence_decay


def assess_fragility_decay() -> dict[str, Any]:
    return assess_fragility_confidence_decay()
