# SPDX-License-Identifier: Apache-2.0
"""Arbiter API — start sessions, retrieve results, inspect the configured pool.

Routes are mounted under ``/api/v1`` by ``aethos_core.api.main`` (the resource
segment ``/arbiter`` lives here, matching the house convention).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from aethos_core.arbiter.models import ArbiterStatus
from aethos_core.arbiter.pool import parse_model_pool, validate_pool
from aethos_core.arbiter.service import run_arbiter_session
from aethos_core.arbiter.session_store import delete_session, get_session, list_sessions
from aethos_core.config import get_settings
from aethos_core.runtime_config.effective_settings import effective_attr, effective_bool, effective_str

router = APIRouter(tags=["arbiter"])
_log = logging.getLogger("aethos.api.arbiter")


class StartArbiterRequest(BaseModel):
    prompt: str
    session_id: str = "default"
    # Debate mode: 0 = single pass; >0 runs that many revise→re-critique rounds
    # (clamped server-side to arbiter_max_debate_rounds).
    debate_rounds: int = 0


class StartArbiterResponse(BaseModel):
    # ``model_count`` would otherwise collide with pydantic's protected
    # ``model_`` namespace; disable the guard for this response shape.
    model_config = ConfigDict(protected_namespaces=())

    arbiter_session_id: str
    status: str
    model_count: int
    message: str


@router.get("/arbiter/status")
async def arbiter_status():
    """Is the arbiter enabled and is the configured pool valid?"""
    s = get_settings()
    enabled = effective_bool("ARBITER_ENABLED")
    pool = parse_model_pool()
    validation = validate_pool(pool)
    # §4 — surface the user's connected models so the panel can offer a checklist,
    # and report whether the active pool came from an explicit selection or the
    # connected-models default.
    explicit_pool = bool(effective_str("ARBITER_MODEL_POOL").strip())
    available_models: list[dict[str, object]] = []
    try:
        from aethos_core.arbiter.pool import supported_providers
        from aethos_core.llm.model_catalog import list_available_models

        supported = supported_providers()
        for row in list_available_models(include_unconfigured=False):
            if str(row.get("id")) == "default":
                continue
            provider = str(row.get("provider") or "").strip().lower()
            model_id = str(row.get("model") or "").strip()
            if not model_id or provider not in supported:
                continue
            available_models.append(
                {
                    "provider": provider,
                    "model_id": model_id,
                    "label": str(row.get("label") or f"{provider}:{model_id}"),
                    "pool_id": f"{provider}:{model_id}",
                }
            )
    except Exception:
        available_models = []
    return {
        "enabled": enabled,
        "pool": pool,
        "pool_valid": validation["valid"],
        "pool_errors": validation.get("errors", []),
        "available_models": available_models,
        "pool_source": "explicit" if explicit_pool else "connected_models_default",
        "config": {
            "consensus_threshold": getattr(s, "arbiter_consensus_threshold", 0.6),
            "max_rounds": getattr(s, "arbiter_max_rounds", 1),
            "max_models": getattr(s, "arbiter_max_models", 8),
            "blind_critique": effective_attr("arbiter_blind_critique", True),
            "timeout_sec": getattr(s, "arbiter_timeout_sec", 180.0),
        },
    }


@router.post("/arbiter/sessions", response_model=StartArbiterResponse)
async def start_arbiter_session(req: StartArbiterRequest):
    """Run a new arbiter session and return its terminal result.

    The session runs inline (dispatch → critique → consensus) and the full
    result is also retrievable via ``/arbiter/sessions/{id}`` and
    ``/arbiter/sessions/{id}/consensus``.
    """
    if not effective_bool("ARBITER_ENABLED"):
        raise HTTPException(status_code=503, detail="Arbiter is disabled. Set ARBITER_ENABLED=true.")

    pool = parse_model_pool()
    validation = validate_pool(pool)
    if not validation["valid"]:
        raise HTTPException(
            status_code=400, detail=f"Arbiter pool invalid: {'; '.join(validation['errors'])}"
        )

    if not req.prompt.strip():
        raise HTTPException(status_code=422, detail="prompt must not be empty")

    result_session = await run_arbiter_session(
        req.prompt.strip(), chat_session_id=req.session_id, debate_rounds=req.debate_rounds
    )

    return StartArbiterResponse(
        arbiter_session_id=result_session.session_id,
        status=result_session.status.value,
        model_count=len(result_session.responses),
        message=(
            result_session.consensus.summary
            if result_session.consensus
            else (result_session.error or "Session completed.")
        ),
    )


@router.post("/arbiter/sessions/start", response_model=StartArbiterResponse)
def start_arbiter_session_async(req: StartArbiterRequest):
    """Start an arbiter session in the BACKGROUND and return its id immediately.

    A multi-round, multi-model debate can run for minutes — longer than the gateway
    request timeout — so holding one synchronous request (POST /arbiter/sessions)
    502s even though the run completes server-side. This endpoint seeds the session,
    kicks the run off on a worker thread, and returns the id so the UI polls
    /arbiter/sessions/{id}/consensus (the run persists to that same session).
    """
    import asyncio
    import threading
    import uuid

    from aethos_core.arbiter.models import ArbiterSession, ArbiterStatus
    from aethos_core.arbiter.session_store import get_session, put_session
    from aethos_core.tenancy import get_current_tenant, tenant_scope

    if not effective_bool("ARBITER_ENABLED"):
        raise HTTPException(status_code=503, detail="Arbiter is disabled. Set ARBITER_ENABLED=true.")
    pool = parse_model_pool()
    validation = validate_pool(pool)
    if not validation["valid"]:
        raise HTTPException(
            status_code=400, detail=f"Arbiter pool invalid: {'; '.join(validation['errors'])}"
        )
    prompt = req.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="prompt must not be empty")

    sid = f"arb-{uuid.uuid4().hex[:12]}"
    owner = get_current_tenant() or "default"
    chat_sid = req.session_id
    rounds = req.debate_rounds

    # Seed a pending session so the UI's poll finds it immediately, before any model responds.
    put_session(
        ArbiterSession(
            session_id=sid,
            chat_session_id=chat_sid,
            tenant_id=owner,
            prompt=prompt,
            status=ArbiterStatus.PENDING,
        )
    )

    def _worker() -> None:
        # Worker threads don't inherit the request tenant contextvar — re-establish it.
        with tenant_scope(owner):
            try:
                asyncio.run(
                    run_arbiter_session(
                        prompt, chat_session_id=chat_sid, debate_rounds=rounds, session_id=sid
                    )
                )
            except Exception:  # noqa: BLE001
                sess = get_session(sid)
                if sess is not None:
                    sess.status = ArbiterStatus.FAILED
                    sess.error = "Arbiter run failed."
                    sess.completed_at = __import__("time").time()
                    put_session(sess)

    threading.Thread(target=_worker, name=f"arbiter-{sid}", daemon=True).start()
    return StartArbiterResponse(
        arbiter_session_id=sid,
        status="running",
        model_count=len(pool),
        message="Arbiter session started.",
    )


@router.get("/arbiter/sessions")
async def list_arbiter_sessions(limit: int = 20):
    return {"sessions": list_sessions(limit=min(limit, 50))}


@router.get("/arbiter/sessions/{session_id}")
async def get_arbiter_session(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Arbiter session {session_id!r} not found.")
    return session.to_dict()


def _critique_scorecard(session) -> list[dict]:
    """Flatten the critique matrix into a readable scorecard: who scored whom, the
    recommend vote, and the critic's own words. This is the judgment BEHIND the
    agreement %, which was previously computed but never exposed."""
    # model_id → human label, and response_id → the answer's model label.
    id_to_label = {m.get("model_id"): m.get("label") for m in session.model_pool}
    resp_label = {r.response_id: r.model_label for r in session.responses}
    rows: list[dict] = []
    for c in session.critiques:
        if c.error:
            continue
        rows.append(
            {
                "critic": id_to_label.get(c.critic_model_id, c.critic_model_id),
                "target": resp_label.get(c.target_response_id, "?"),
                "overall_score": round(c.overall_score, 3),
                "accuracy_score": round(c.accuracy_score, 3),
                "completeness_score": round(c.completeness_score, 3),
                "reasoning_score": round(c.reasoning_score, 3),
                "recommended": c.recommended,
                "critique": c.critique_text,
            }
        )
    # Highest-scoring critiques first so the strongest signal is on top.
    rows.sort(key=lambda r: r["overall_score"], reverse=True)
    return rows


@router.get("/arbiter/sessions/{session_id}/consensus")
async def get_consensus(session_id: str):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Arbiter session {session_id!r} not found.")
    if session.status in (
        ArbiterStatus.PENDING,
        ArbiterStatus.DISPATCHING,
        ArbiterStatus.CRITIQUING,
    ):
        return {"status": session.status.value, "message": "Session still running."}
    if not session.consensus:
        return {"status": session.status.value, "message": session.error or "No consensus data."}
    return {
        "status": session.status.value,
        "consensus": {
            "reached": session.consensus.consensus_reached,
            "agreement_score": session.consensus.agreement_score,
            "winning_model": session.consensus.winning_model_label,
            "winning_text": session.consensus.winning_text,
            "summary": session.consensus.summary,
            "agreeing_models": session.consensus.agreeing_models,
            "dissenting_model_ids": session.consensus.dissenting_model_ids,
        },
        "responses": [
            {
                "model_label": r.model_label,
                "response_id": r.response_id,
                "text_preview": r.text[:2000] if r.text else None,
                "latency_ms": r.latency_ms,
                "error": r.error,
            }
            for r in session.responses
        ],
        # The judgment behind the score: per-critic→target reasoning + recommend votes.
        "critiques": _critique_scorecard(session),
        # Iterative peer-review history (empty unless debate rounds were requested).
        "debate_rounds": session.debate_rounds,
        "rounds_completed": session.rounds_completed,
    }


@router.delete("/arbiter/sessions/{session_id}")
async def delete_arbiter_session(session_id: str):
    removed = delete_session(session_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found.")
    return {"deleted": True, "session_id": session_id}
