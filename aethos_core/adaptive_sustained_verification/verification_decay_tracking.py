# SPDX-License-Identifier: Apache-2.0
"""Verification decay tracking — trust erosion."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_verification.verification_decay import assess_verification_decay


def track_verification_decay() -> dict[str, Any]:
    return assess_verification_decay()
