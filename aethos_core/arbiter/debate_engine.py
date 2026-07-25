# SPDX-License-Identifier: Apache-2.0
"""
Debate / revision round — the missing "back-and-forth" step.

After the critique round, each model is shown the peer critiques of ITS OWN answer
(plus the other answers, blind) and asked to REVISE — defending what holds up,
fixing what doesn't. The revised answers then go back through critique + consensus.

This turns the arbiter from a one-shot parallel sample into an iterative peer-review
that stress-tests the plan across turns, with the human as the final arbiter. It
reuses the dispatcher's provider path (``_sync_complete``) — no new HTTP logic.

Cost note: each debate round = one revise call per model + one critique pass. The
caller caps the round count (``arbiter_max_debate_rounds``) so a tenant paying for
their own keys can't fan out unbounded.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict

from aethos_core.arbiter.models import CritiqueScore, ModelResponse
from aethos_core.config import get_settings

_log = logging.getLogger("aethos.arbiter.debate")

_REVISE_TIMEOUT_SEC = 60.0

_REVISE_SYSTEM = """\
You are in a multi-model peer-review debate. You previously answered a prompt and \
other expert models critiqued your answer. Produce an IMPROVED answer:
- Address every valid criticism; strengthen weak or unsupported claims.
- If a criticism is wrong, hold your position — but say briefly why.
- Incorporate any genuinely better ideas visible in the other answers.
- Do not pad or restate the prompt. Output ONLY your revised answer.
"""


def _critiques_for(response_id: str, critiques: list[CritiqueScore]) -> list[CritiqueScore]:
    return [c for c in critiques if c.target_response_id == response_id and not c.error]


def _build_revision_prompt(
    original_prompt: str,
    own: ModelResponse,
    own_critiques: list[CritiqueScore],
    peers: list[ModelResponse],
) -> str:
    crit_lines = []
    for c in own_critiques:
        verdict = "recommended" if c.recommended else "not recommended"
        crit_lines.append(
            f"- (score {c.overall_score:.2f}/1.0, {verdict}) {c.critique_text or '(no comment)'}"
        )
    crit_block = "\n".join(crit_lines) if crit_lines else "- (no critiques were recorded)"

    peer_block_parts = []
    for i, p in enumerate(peers):
        peer_block_parts.append(f"Answer {chr(65 + i)}:\n{p.text}")
    peer_block = "\n\n".join(peer_block_parts) if peer_block_parts else "(none)"

    return (
        f"{_REVISE_SYSTEM}\n\n"
        f"Original prompt:\n{original_prompt}\n\n"
        f"---\nYour previous answer:\n{own.text}\n\n"
        f"---\nPeer critiques of your previous answer:\n{crit_block}\n\n"
        f"---\nOther answers under review (anonymized):\n{peer_block}\n\n"
        f"---\nWrite your improved answer now."
    )


async def _revise_one(
    entry: dict[str, str],
    original_prompt: str,
    own: ModelResponse,
    own_critiques: list[CritiqueScore],
    peers: list[ModelResponse],
    *,
    tenant_id: str | None = None,
) -> ModelResponse:
    from aethos_core.arbiter.dispatcher import _sync_complete

    prompt = _build_revision_prompt(original_prompt, own, own_critiques, peers)
    started = time.time()
    try:
        loop = asyncio.get_running_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None, _sync_complete, entry["provider"], entry["model_id"], prompt, tenant_id
            ),
            timeout=_REVISE_TIMEOUT_SEC,
        )
        text = (result.get("text") or "").strip()
        if not text:
            # Keep the prior answer rather than dropping the model from the round.
            return own
        return ModelResponse(
            response_id=f"resp-rev-{entry['model_id'][:8].replace('/', '-')}-{int(started * 1000) % 100000}",
            provider=entry["provider"],
            model_id=entry["model_id"],
            model_label=entry["label"],
            text=text,
            latency_ms=int((time.time() - started) * 1000),
            used_llm=result.get("used_llm", True),
            error=result.get("error"),
        )
    except asyncio.TimeoutError:
        _log.warning("Arbiter revise: %s timed out", entry["model_id"])
        return own  # fall back to the un-revised answer
    except Exception as exc:  # noqa: BLE001 — never crash a round
        _log.warning("Arbiter revise: %s failed: %s", entry["model_id"], exc.__class__.__name__)
        return own


async def run_revision_round(
    pool: list[dict[str, str]],
    original_prompt: str,
    responses: list[ModelResponse],
    critiques: list[CritiqueScore],
    *,
    tenant_id: str | None = None,
) -> list[ModelResponse]:
    """Each model revises its own answer given the peer critiques + other answers.

    Returns a new ModelResponse list (same models). Models that errored or have no
    text are passed through unchanged; revision failures fall back to the prior answer.
    """
    by_model = {entry["model_id"]: entry for entry in pool}
    valid = [r for r in responses if not r.error and r.text]
    if len(valid) < 2:
        return responses

    crit_by_target: dict[str, list[CritiqueScore]] = defaultdict(list)
    for c in critiques:
        crit_by_target[c.target_response_id].append(c)

    tasks: list[asyncio.Task[ModelResponse]] = []
    revisable: list[ModelResponse] = []
    for r in valid:
        entry = by_model.get(r.model_id)
        if not entry:
            continue
        peers = [p for p in valid if p.response_id != r.response_id]
        revisable.append(r)
        tasks.append(
            asyncio.ensure_future(
                _revise_one(
                    entry, original_prompt, r, _critiques_for(r.response_id, crit_by_target.get(r.response_id, [])), peers,
                    tenant_id=tenant_id,
                )
            )
        )

    if not tasks:
        return responses

    s = get_settings()
    budget = float(getattr(s, "arbiter_timeout_sec", 180.0) or 180.0) * 0.5
    try:
        revised = await asyncio.wait_for(asyncio.gather(*tasks), timeout=budget)
    except asyncio.TimeoutError:
        _log.warning("Arbiter revision round hit timeout at %.0fs", budget)
        revised = []
        for task, original in zip(tasks, revisable):
            revised.append(task.result() if (task.done() and task.exception() is None) else original)
            if not task.done():
                task.cancel()

    # Preserve any errored/empty responses that we skipped, plus the revised ones.
    revised_by_model = {r.model_id: r for r in revised}
    return [revised_by_model.get(r.model_id, r) for r in responses]
