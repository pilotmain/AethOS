# SPDX-License-Identifier: Apache-2.0
"""Verification fatigue — verification exhaustion."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_fatigue_intelligence.verification_fatigue import assess_verification_fatigue


def assess_verification_exhaustion() -> dict[str, Any]:
    return assess_verification_fatigue()
