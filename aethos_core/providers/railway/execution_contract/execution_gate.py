# SPDX-License-Identifier: Apache-2.0
"""Execution gate — delegates to the authoritative execution readiness gate."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.execution_readiness_gate import (
    RailwayExecutionReadinessGate,
    evaluate_railway_execution_readiness,
)


def build_execution_gate_assessment(
    *,
    plan: dict[str, Any] | None,
    preflight: dict[str, Any] | None,
    simulation: dict[str, Any] | None,
    session_id: str = "default",
    text: str | None = None,
) -> dict[str, Any]:
    gate = evaluate_railway_execution_readiness(
        session_id,
        text,
        plan=plan,
        preflight=preflight,
        simulation=simulation,
    )
    return gate.to_assessment_dict()
