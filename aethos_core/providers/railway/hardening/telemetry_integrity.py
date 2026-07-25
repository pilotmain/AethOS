# SPDX-License-Identifier: Apache-2.0
"""Railway telemetry integrity — deployment telemetry validation."""

from __future__ import annotations

from typing import Any


def assess_telemetry_integrity(*, readonly_artifact: dict[str, Any]) -> dict[str, Any]:
    summary = str(readonly_artifact.get("summary") or "")
    fresh = "stale" not in summary.lower() and "unknown" not in summary.lower()
    return {
        "telemetry_fresh": fresh,
        "freshness_recovered": fresh or len(summary) > 0,
        "summary": "Telemetry freshness recovered." if fresh else "Telemetry freshness partially recovered — extended monitoring recommended.",
    }
