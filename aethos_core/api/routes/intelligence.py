# SPDX-License-Identifier: Apache-2.0
"""Operational intelligence API — anomalies, recommendations, drift, replay."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["intelligence"])


class SnoozeRequest(BaseModel):
    hours: float = 4.0


class GeneratePreflightRequest(BaseModel):
    workspace_hint: str = "aethos"


@router.get("/intelligence/state")
def intelligence_state_api() -> dict[str, Any]:
    from aethos_core.operations.reality_loop import get_operational_intelligence_state
    from aethos_core.intelligence.operational_replay import list_operational_replays
    from aethos_core.runtime.schedulers.observation_scheduler import scheduler_status

    state = get_operational_intelligence_state()
    state["replays"] = list_operational_replays(limit=10)
    state["scheduler"] = scheduler_status()
    return state


@router.get("/intelligence/anomalies")
def intelligence_anomalies_api() -> dict[str, Any]:
    from aethos_core.intelligence.anomaly_engine import detect_operational_anomalies
    from aethos_core.operations.reality_loop import collect_operational_observations

    observations = collect_operational_observations()
    anomalies = detect_operational_anomalies(observations=observations)
    return {"ok": True, "anomalies": anomalies, "readonly": True}


@router.get("/intelligence/recommendations")
def intelligence_recommendations_api() -> dict[str, Any]:
    from aethos_core.intelligence.recommendations import list_recommendations

    return {"ok": True, "recommendations": list_recommendations(), "autonomous_execution_blocked": True}


@router.get("/intelligence/drift")
def intelligence_drift_api() -> dict[str, Any]:
    from aethos_core.operations.reality_loop import collect_operational_observations, detect_operational_drift

    observations = collect_operational_observations()
    return {"ok": True, "drift": detect_operational_drift(observations)}


@router.get("/intelligence/stability")
def intelligence_stability_api() -> dict[str, Any]:
    from aethos_core.operations.reality_loop import collect_operational_observations, deployment_stability_snapshot

    observations = collect_operational_observations()
    return {"ok": True, "stability": deployment_stability_snapshot(observations)}


@router.get("/intelligence/replay/{replay_id}")
def intelligence_replay_api(replay_id: str) -> dict[str, Any]:
    from aethos_core.intelligence.operational_replay import get_operational_replay

    replay = get_operational_replay(replay_id)
    if not replay:
        raise HTTPException(status_code=404, detail="replay_not_found")
    return {"ok": True, "replay": replay}


@router.post("/intelligence/cycle")
def intelligence_cycle_api() -> dict[str, Any]:
    from aethos_core.operations.reality_loop import run_reality_loop_cycle

    cycle = run_reality_loop_cycle(source="api")
    return {"ok": True, "cycle": cycle}


@router.post("/intelligence/recommendations/{recommendation_id}/dismiss")
def dismiss_recommendation_api(recommendation_id: str) -> dict[str, Any]:
    from aethos_core.intelligence.recommendations import dismiss_recommendation

    result = dismiss_recommendation(recommendation_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "dismiss_failed")
    return result


@router.post("/intelligence/recommendations/{recommendation_id}/snooze")
def snooze_recommendation_api(recommendation_id: str, body: SnoozeRequest | None = None) -> dict[str, Any]:
    from aethos_core.intelligence.recommendations import snooze_recommendation

    hours = body.hours if body else 4.0
    result = snooze_recommendation(recommendation_id, hours=hours)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("error") or "snooze_failed")
    return result


@router.post("/intelligence/recommendations/{recommendation_id}/generate-preflight")
def generate_preflight_from_recommendation_api(
    recommendation_id: str,
    body: GeneratePreflightRequest | None = None,
) -> dict[str, Any]:
    from aethos_core.intelligence.recommendations import generate_preflight_from_recommendation

    hint = body.workspace_hint if body else "aethos"
    result = generate_preflight_from_recommendation(recommendation_id, repo_hint=hint)
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "preflight_failed")
    return result
