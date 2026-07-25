# SPDX-License-Identifier: Apache-2.0
"""Operational reliability intelligence — Phase 11.3 aggregate runtime."""

from __future__ import annotations

from typing import Any

from aethos_core.continuous_verification.runtime import assess_continuous_verification
from aethos_core.drift_intelligence.runtime import assess_drift_intelligence
from aethos_core.predictive_operations.runtime import assess_predictive_operations
from aethos_core.production_confidence.runtime import assess_production_confidence
from aethos_core.recovery_orchestration.runtime import orchestrate_recovery
from aethos_core.reliability_harness.harness_runtime import harness_state
from aethos_core.reliability_memory.runtime import assess_reliability_memory


def assess_operational_reliability(*, runtime_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    """Continuous operational reliability assurance across Phase 11.3 slices."""
    verification = assess_continuous_verification(runtime_snapshot=runtime_snapshot)
    recovery = orchestrate_recovery(runtime_snapshot=runtime_snapshot)
    drift = assess_drift_intelligence(runtime_snapshot=runtime_snapshot)
    predictive = assess_predictive_operations(runtime_snapshot=runtime_snapshot)
    confidence = assess_production_confidence(runtime_snapshot=runtime_snapshot)
    memory = assess_reliability_memory(runtime_snapshot=runtime_snapshot)
    harness = harness_state()
    production_reliable = (
        verification.get("sustained")
        and confidence.get("trust", {}).get("qualification_tier") in ("stable", "production-ready", "production-reliable")
        and drift.get("drift_bounded")
    )
    return {
        "ok": True,
        "phase": "11.3",
        "harness_version": harness.get("harness_version"),
        "production_reliable": production_reliable,
        "continuous_verification": verification,
        "recovery_orchestration": recovery,
        "drift_intelligence": drift,
        "predictive_operations": predictive,
        "production_confidence": confidence,
        "reliability_memory": memory,
        "harness": harness,
        "capabilities": _capability_summary(verification, recovery, drift, confidence),
        "summary": confidence.get("narrative", ""),
    }


def _capability_summary(
    verification: dict[str, Any],
    recovery: dict[str, Any],
    drift: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, str]:
    return {
        "continuous_verification": verification.get("maturity", "beta"),
        "recovery_orchestration": recovery.get("maturity", "beta"),
        "drift_intelligence": drift.get("maturity", "beta"),
        "predictive_operations": "stable" if confidence.get("predictive", {}).get("predictive_awareness") else "beta",
        "production_confidence": confidence.get("trust", {}).get("qualification_tier", "beta"),
        "reliability_memory": "stable",
    }
