# SPDX-License-Identifier: Apache-2.0
"""Adaptive decay detection — operational erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.adaptive_sustained_verification.verification_decay_tracking import track_verification_decay


def detect_adaptive_decay() -> dict[str, Any]:
    return track_verification_decay()
