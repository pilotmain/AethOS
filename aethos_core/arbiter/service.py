# SPDX-License-Identifier: Apache-2.0
"""
ArbiterService — public entry point for starting and running arbiter sessions.

Orchestrates: pool validation → dispatch → critique → consensus → artifact.
All async. Called from the API route and optionally from the chat lane.
Never raises — errors are stored on the returned session.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from aethos_core.arbiter.consensus_engine import compute_consensus
from aethos_core.arbiter.critique_engine import run_critique_round
from aethos_core.arbiter.dispatcher import dispatch_to_pool
from aethos_core.arbiter.models import ArbiterSession, ArbiterStatus
from aethos_core.arbiter.pool import parse_model_pool, validate_pool
from aethos_core.arbiter.session_store import put_session
from aethos_core.config import get_settings
from aethos_core.runtime_config.effective_settings import effective_attr, effective_bool

_log = logging.getLogger("aethos.arbiter.service")


async def run_arbiter_session(
    prompt: str,
    *,
    chat_session_id: str = "default",
    model_pool_override: list[dict[str, str]] | None = None,
    fast: bool = False,
    debate_rounds: int = 0,
    session_id: str | None = None,
) -> ArbiterSession:
    """
    Full arbiter lifecycle: dispatch → critique → [debate: revise → re-critique]* → consensus.
    Returns the completed ArbiterSession regardless of outcome.

    ``debate_rounds`` (capped by ``arbiter_max_debate_rounds``) runs iterative peer
    review: each model revises its answer given the critiques, then the pool re-critiques.
    The final consensus is computed on the stress-tested answers. 0 = single pass.
    """
    s = get_settings()

    # When an async caller pre-created the session id (start endpoint), reuse it for
    # every ArbiterSession we build so the in-flight session the UI is polling is the
    # same one we update — including early error returns.
    def _mk(**kw: Any) -> ArbiterSession:
        if session_id:
            kw["session_id"] = session_id
        return ArbiterSession(**kw)

    # Stamp the owning tenant at creation. Even though run_arbiter_session is
    # async (and may carry the request ContextVar), the model fan-out happens in
    # executor threads that do NOT inherit it, so we capture the tenant here and
    # thread it through dispatch/critique (Correction 1).
    from aethos_core.tenancy import get_current_tenant

    tenant_id = get_current_tenant()

    # Per-tenant abuse ceiling (Correction 4): cap a single tenant's arbiter
    # runs/hour so one user cannot run up the operator's compute via parallel
    # fan-out. Operator/default tenant is exempt; no-op unless multi-tenant.
    from aethos_core.tenancy.tenant_limits import check_arbiter_run

    allowed, retry_after = check_arbiter_run(tenant_id)
    if not allowed:
        session = _mk(chat_session_id=chat_session_id, tenant_id=tenant_id, prompt=prompt)
        session.status = ArbiterStatus.FAILED
        session.error = (
            f"Arbiter rate limit reached for this account "
            f"({s.tenant_arbiter_runs_per_hour}/hour). Try again in ~{retry_after}s."
        )
        session.completed_at = time.time()
        put_session(session)
        return session

    if not effective_bool("ARBITER_ENABLED"):
        session = _mk(chat_session_id=chat_session_id, tenant_id=tenant_id, prompt=prompt)
        session.status = ArbiterStatus.FAILED
        session.error = (
            "Arbiter is disabled. Set ARBITER_ENABLED=true and configure ARBITER_MODEL_POOL."
        )
        session.completed_at = time.time()
        put_session(session)
        return session

    pool = model_pool_override or parse_model_pool()
    validation = validate_pool(pool)
    if not validation["valid"]:
        session = _mk(
            chat_session_id=chat_session_id, tenant_id=tenant_id, prompt=prompt, model_pool=pool
        )
        session.status = ArbiterStatus.FAILED
        session.error = "; ".join(validation["errors"])
        session.completed_at = time.time()
        put_session(session)
        return session

    session = _mk(
        chat_session_id=chat_session_id,
        tenant_id=tenant_id,
        prompt=prompt,
        model_pool=pool,
        status=ArbiterStatus.DISPATCHING,
    )
    put_session(session)

    try:
        # ── Round 0: Parallel dispatch ───────────────────────────────────────
        _log.info("Arbiter %s: dispatching to %d models", session.session_id, len(pool))
        responses = await dispatch_to_pool(pool, prompt, tenant_id=session.tenant_id)
        session.responses = responses
        session.rounds_completed = 1

        valid_count = sum(1 for r in responses if not r.error)
        if valid_count == 0:
            session.status = ArbiterStatus.FAILED
            session.error = "All models in pool failed to respond."
            session.completed_at = time.time()
            put_session(session)
            return session

        # ── Round 1: Critique ────────────────────────────────────────────────
        # Fast mode skips the peer-critique round (the expensive phase: each model
        # critiques the others). You still get every model's answer in parallel; you
        # just don't get the cross-critique ranking. Big latency win when you want speed.
        max_rounds = int(getattr(s, "arbiter_max_rounds", 1) or 1)
        blind = bool(effective_attr("arbiter_blind_critique", True))

        if not fast and max_rounds >= 1 and valid_count >= 2:
            session.status = ArbiterStatus.CRITIQUING
            put_session(session)
            _log.info("Arbiter %s: critique round (blind=%s)", session.session_id, blind)
            critiques = await run_critique_round(
                pool, prompt, responses, blind=blind, tenant_id=session.tenant_id
            )
            session.critiques = critiques
            session.rounds_completed = 2

        # ── Debate: revise → re-critique loop ────────────────────────────────
        # Iterative peer review. Needs critiques to revise against, so it only runs
        # when a critique round happened (not in fast mode). Capped so a BYOK tenant
        # cannot fan out unbounded.
        threshold = float(getattr(s, "arbiter_consensus_threshold", 0.6) or 0.6)
        max_debate = int(getattr(s, "arbiter_max_debate_rounds", 3) or 0)
        rounds = max(0, min(int(debate_rounds or 0), max_debate))
        if rounds and session.critiques and valid_count >= 2:
            from aethos_core.arbiter.debate_engine import run_revision_round

            for n in range(1, rounds + 1):
                live = sum(1 for r in responses if not r.error and r.text)
                if live < 2:
                    break
                _log.info("Arbiter %s: debate round %d/%d", session.session_id, n, rounds)
                responses = await run_revision_round(
                    pool, prompt, responses, session.critiques, tenant_id=session.tenant_id
                )
                session.responses = responses
                session.critiques = await run_critique_round(
                    pool, prompt, responses, blind=blind, tenant_id=session.tenant_id
                )
                session.rounds_completed += 2
                round_consensus = compute_consensus(
                    responses, session.critiques, threshold=threshold
                )
                session.debate_rounds.append(
                    {
                        "round": n,
                        "agreement_score": round_consensus.agreement_score,
                        "consensus_reached": round_consensus.consensus_reached,
                        "winning_model": round_consensus.winning_model_label,
                        "answers": [
                            {"model_label": r.model_label, "text_preview": (r.text or "")[:600]}
                            for r in responses
                            if not r.error and r.text
                        ],
                    }
                )
                put_session(session)

        # ── Consensus ────────────────────────────────────────────────────────
        session.status = ArbiterStatus.CONSENSUS
        consensus = compute_consensus(responses, session.critiques, threshold=threshold)
        session.consensus = consensus
        session.status = (
            ArbiterStatus.COMPLETED if consensus.consensus_reached else ArbiterStatus.NO_CONSENSUS
        )
        session.completed_at = time.time()

        _store_artifact(session)
        put_session(session)

        _log.info(
            "Arbiter %s: %s in %dms (agreement=%.0f%%)",
            session.session_id,
            session.status.value,
            session.duration_ms,
            consensus.agreement_score * 100,
        )

    except Exception as exc:
        _log.exception("Arbiter %s: unexpected error: %s", session.session_id, exc)
        session.status = ArbiterStatus.FAILED
        session.error = str(exc)
        session.completed_at = time.time()
        put_session(session)

    return session


def _store_artifact(session: ArbiterSession) -> None:
    """Store the arbiter session as a governed agent artifact for the audit trail."""
    try:
        from aethos_core.agents.runtime.artifacts import store_agent_artifact

        persist_full = bool(getattr(get_settings(), "arbiter_persist_full_responses", True))

        payload: dict[str, Any] = {
            "session_id": session.session_id,
            "prompt_preview": session.prompt[:500],
            "model_pool": session.model_pool,
            "response_count": len(session.responses),
            "critique_count": len(session.critiques),
            "debate_round_count": len(session.debate_rounds),
            "consensus": session.consensus.__dict__ if session.consensus else None,
            "status": session.status.value,
            "duration_ms": session.duration_ms,
        }

        if persist_full:
            payload["responses"] = [
                {
                    "response_id": r.response_id,
                    "model_label": r.model_label,
                    "text_preview": r.text[:1000] if r.text else None,
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                }
                for r in session.responses
            ]

        artifact = store_agent_artifact(
            artifact_type="arbiter_session",
            agent_id="arbiter",
            plan_id=None,
            payload=payload,
            summary=(
                session.consensus.summary
                if session.consensus
                else f"Arbiter session {session.status.value}"
            ),
        )
        session.artifact_id = artifact["artifact_id"]
    except Exception as exc:
        _log.warning("Arbiter: failed to store artifact: %s", exc)
