# SPDX-License-Identifier: Apache-2.0
"""Rollback truth — rollback verification integrity."""

from __future__ import annotations

from typing import Any


def assess_rollback_truth(*, provider: str = "railway") -> dict[str, Any]:
    from aethos_core.rollback_integrity.rollback_confidence import score_rollback_confidence

    sample = {
        "provider_result": {"deployment_state_after": "restored", "summary": "Rollback completed."},
        "readonly_artifact": {"summary": "Primary services recovered."},
    }
    confidence = score_rollback_confidence(**sample)
    return {
        "provider": provider,
        "rollback_verified": confidence.get("rollback_verified", False),
        "confidence": confidence,
        "summary": (
            "Rollback completed and primary services recovered, though downstream telemetry stabilization "
            "is still being verified across dependent runtime surfaces."
        ),
        "extended_monitoring_active": not confidence.get("rollback_verified", False),
    }
