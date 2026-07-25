# SPDX-License-Identifier: Apache-2.0
"""Drift detection — runtime configuration drift."""

from __future__ import annotations

from typing import Any


def detect_runtime_drift(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    drift_signals = runtime_snapshot.get("drift_signals") or []
    if not isinstance(drift_signals, list):
        drift_signals = []
    config_hash = runtime_snapshot.get("config_hash")
    desired_hash = runtime_snapshot.get("desired_config_hash")
    hash_drift = bool(config_hash and desired_hash and config_hash != desired_hash)
    return {
        "drift_detected": bool(drift_signals) or hash_drift,
        "drift_signals": drift_signals,
        "config_hash_drift": hash_drift,
        "summary": "No configuration drift detected." if not drift_signals and not hash_drift else "Runtime configuration drift detected.",
    }
