# SPDX-License-Identifier: Apache-2.0
"""Recovery window runtime — extended recovery validation."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_patience.recovery_observation import observe_recovery


def validate_recovery_window() -> dict[str, Any]:
    return observe_recovery(hours_observed=3.0, hours_required=4.0)
