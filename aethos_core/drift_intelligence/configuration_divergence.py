# SPDX-License-Identifier: Apache-2.0
"""Configuration divergence — infrastructure drift."""

from __future__ import annotations

from typing import Any


def detect_configuration_divergence(*, reconciliation: dict[str, Any]) -> dict[str, Any]:
    state_diff = reconciliation.get("state_diff") or {}
    k8s_drift = reconciliation.get("kubernetes", {}).get("drift") or {}
    diverged = not state_diff.get("aligned", True) or k8s_drift.get("drift_detected", False)
    return {
        "diverged": diverged,
        "missing": state_diff.get("missing") or [],
        "extra": state_diff.get("extra") or [],
        "summary": "Configuration divergence detected." if diverged else "Configuration aligned with desired state.",
    }
