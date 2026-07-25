# SPDX-License-Identifier: Apache-2.0
"""Stabilization windows — extended verification periods."""

from __future__ import annotations

from typing import Any

DEFAULT_WINDOW_MINUTES = 15
EXTENDED_WINDOW_MINUTES = 45


def assess_stabilization_window(*, verification: dict[str, Any] | None = None) -> dict[str, Any]:
    verification = verification or {}
    verified = bool(verification.get("verified"))
    return {
        "default_window_minutes": DEFAULT_WINDOW_MINUTES,
        "extended_window_minutes": EXTENDED_WINDOW_MINUTES,
        "extended_monitoring_active": not verified,
        "stabilization_complete": verified,
        "summary": "Extended monitoring remains active across stabilization window."
        if not verified
        else "Stabilization window satisfied.",
    }
