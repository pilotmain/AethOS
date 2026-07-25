# SPDX-License-Identifier: Apache-2.0
"""Recovery storytelling — calm operational explanation."""

from __future__ import annotations

from typing import Any


def build_recovery_story(
    *,
    resolved: bool,
    extended_monitoring: bool,
    recovery_confidence: float,
) -> str:
    if resolved and not extended_monitoring:
        return (
            "Operational stability improved after recovery actions. "
            "Verification and reconciliation confirm stabilization."
        )
    return (
        "Operational stability improved after recovery actions, "
        "though extended monitoring remains active to ensure replay continuity "
        "and telemetry consistency remain stable over time."
    )
