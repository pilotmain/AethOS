# SPDX-License-Identifier: Apache-2.0
"""Stabilization patience — runtime convergence pacing."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_stabilization.recovery_patience import assess_recovery_patience


def assess_stabilization_patience(*, stabilization: dict[str, Any] | None = None) -> dict[str, Any]:
    stabilization = stabilization or {"stabilization_complete": False, "extended_monitoring_active": True}
    verification = {"verified": False}
    return assess_recovery_patience(stabilization=stabilization, verification=verification)
