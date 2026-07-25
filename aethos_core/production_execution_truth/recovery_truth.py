# SPDX-License-Identifier: Apache-2.0
"""Recovery truth — sustained recovery qualification."""

from __future__ import annotations

from typing import Any

from aethos_core.production_execution_truth.stabilization_windows import assess_stabilization_window


def assess_recovery_truth(*, verification: dict[str, Any] | None = None) -> dict[str, Any]:
    window = assess_stabilization_window(verification=verification)
    sustained = window.get("stabilization_complete", False)
    return {
        "sustained_recovery": sustained,
        "extended_monitoring_active": window.get("extended_monitoring_active", True),
        "stabilization_window": window,
        "summary": "Sustained recovery qualification converging."
        if not sustained
        else "Sustained recovery qualified across stabilization window.",
    }
