# SPDX-License-Identifier: Apache-2.0
"""Reliability API — operational trust authority."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["reliability"])


class RecoveryRequest(BaseModel):
    action: str
    operator_id: str = "default"


class ReconstructRequest(BaseModel):
    window_hours: int = 48


@router.get("/reliability/state")
def reliability_state_api() -> dict[str, Any]:
    from aethos_core.reliability.reliability_runtime import get_reliability_state

    return get_reliability_state()


@router.get("/reliability/scores")
def reliability_scores_api() -> dict[str, Any]:
    from aethos_core.reliability.reliability_runtime import assess_operational_reliability

    result = assess_operational_reliability()
    return {"ok": True, "scores": result.get("scores"), "reliability": result.get("reliability")}


@router.get("/reliability/replay")
def reliability_replay_api(window_hours: int = 48) -> dict[str, Any]:
    from aethos_core.replay_intelligence.incident_reconstruction import reconstruct_incident_timeline

    return reconstruct_incident_timeline(window_hours=window_hours)


@router.get("/reliability/confidence")
def reliability_confidence_api() -> dict[str, Any]:
    from aethos_core.reliability.reliability_runtime import assess_operational_reliability

    result = assess_operational_reliability()
    rel = result.get("reliability") or {}
    return {
        "ok": True,
        "confidence": rel.get("confidence_detail"),
        "truth_state": rel.get("truth_state"),
        "explainability": (result.get("explainability") or {}).get("confidence"),
    }


@router.get("/reliability/governance")
def reliability_governance_api() -> dict[str, Any]:
    from aethos_core.reliability.reliability_runtime import assess_operational_reliability

    result = assess_operational_reliability()
    return {
        "ok": True,
        "governance": result.get("governance"),
        "explainability": (result.get("explainability") or {}).get("governance"),
        "autonomous_execution_blocked": True,
    }


@router.get("/reliability/correlation")
def reliability_correlation_api() -> dict[str, Any]:
    from aethos_core.reliability.reliability_runtime import assess_operational_reliability

    result = assess_operational_reliability()
    return {"ok": True, "correlation": result.get("correlation")}


@router.post("/reliability/replay/reconstruct")
def reliability_reconstruct_api(body: ReconstructRequest | None = None) -> dict[str, Any]:
    from aethos_core.replay_intelligence.incident_reconstruction import reconstruct_incident_timeline

    hours = body.window_hours if body else 48
    return reconstruct_incident_timeline(window_hours=hours)


@router.post("/reliability/recovery/retry")
def reliability_recovery_api(body: RecoveryRequest) -> dict[str, Any]:
    from aethos_core.reliability.recovery_runtime import execute_bounded_recovery

    result = execute_bounded_recovery(action=body.action, operator_id=body.operator_id)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "recovery_failed")
    return result
