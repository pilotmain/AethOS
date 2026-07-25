# SPDX-License-Identifier: Apache-2.0
"""Telemetry anomalies — signal inconsistency."""

from __future__ import annotations

from typing import Any


def detect_telemetry_anomalies(*, infrastructure: dict[str, Any]) -> dict[str, Any]:
    k8s = infrastructure.get("kubernetes", {}).get("node_pressure") or {}
    telemetry_ok = k8s.get("telemetry_within_thresholds", True)
    docker_pressure = infrastructure.get("docker", {}).get("pressure", {}).get("elevated_count", 0)
    anomalies = (not telemetry_ok) or docker_pressure > 0
    return {
        "anomalies_detected": anomalies,
        "telemetry_consistent": not anomalies,
        "summary": "Telemetry consistency preserved." if not anomalies else "Telemetry inconsistency signals detected.",
    }
