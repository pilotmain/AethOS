# SPDX-License-Identifier: Apache-2.0
"""Operational truth runtime — unified truth convergence orchestrator."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_truth.capability_audit import run_capability_audit
from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix, matrix_summary
from aethos_core.operational_truth.execution_integrity import assess_execution_integrity
from aethos_core.operational_truth.operational_honesty import assess_operational_honesty
from aethos_core.operational_truth.operational_readiness import assess_operational_readiness


def assess_operational_truth() -> dict[str, Any]:
    """Full operational truth assessment — capability matrix + integrity + readiness."""
    matrix = build_capability_truth_matrix()
    summary = matrix_summary(matrix)
    readiness = assess_operational_readiness()
    integrity = assess_execution_integrity()
    honesty = assess_operational_honesty(matrix)
    audit = run_capability_audit()

    system_truth: dict[str, Any] = {}
    try:
        from aethos_core.reliability.reliability_runtime import assess_operational_reliability

        rel = assess_operational_reliability()
        system_truth = rel.get("reliability") or {}
    except Exception:
        pass

    truth_state = str(system_truth.get("truth_state") or integrity.get("integrity_state") or "operationally_unknown")
    degraded = truth_state not in ("verified_healthy", "verified")

    return {
        "ok": True,
        "truth_state": truth_state,
        "truth_degraded": degraded,
        "capability_matrix": matrix,
        "matrix_summary": summary,
        "readiness": readiness,
        "execution_integrity": integrity,
        "operational_honesty": honesty,
        "capability_audit": audit,
        "system_truth": system_truth,
        "autonomous_execution_blocked": True,
        "summary": _compose_summary(truth_state, readiness, honesty, integrity),
    }


def get_operational_truth_state() -> dict[str, Any]:
    """Lightweight state for Mission Control badges."""
    result = assess_operational_truth()
    return {
        "ok": True,
        "truth_state": result["truth_state"],
        "truth_degraded": result["truth_degraded"],
        "readiness_tier": result["readiness"]["readiness_tier"],
        "readiness_score": result["readiness"]["readiness_score"],
        "verification_coverage_pct": result["readiness"]["verification_coverage_pct"],
        "overclaim_risk": result["operational_honesty"]["overclaim_risk"],
        "summary": result["summary"],
    }


def _compose_summary(
    truth_state: str,
    readiness: dict[str, Any],
    honesty: dict[str, Any],
    integrity: dict[str, Any],
) -> str:
    parts = [
        f"System truth: {truth_state.replace('_', ' ')}.",
        f"Readiness: {readiness['readiness_tier']} ({readiness['readiness_score']}%).",
        integrity.get("summary", ""),
    ]
    if honesty.get("overclaim_risk"):
        parts.append(honesty.get("recommended_phrasing", ""))
    return " ".join(p for p in parts if p)
