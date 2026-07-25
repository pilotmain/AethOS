# SPDX-License-Identifier: Apache-2.0
"""Verification windows — extended stabilization checks."""

from __future__ import annotations

from typing import Any


def active_verification_windows(*, stabilization: dict[str, Any]) -> dict[str, Any]:
    phase = stabilization.get("stabilization_phase") or "monitoring"
    return {
        "windows_active": True,
        "phase": phase,
        "extended_checks": phase != "stabilized",
        "summary": "Extended verification window active for infrastructure stabilization.",
    }
