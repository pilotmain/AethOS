# SPDX-License-Identifier: Apache-2.0
"""
Critique round — each model in the pool reviews the other models' responses
and assigns structured scores. This is the "arbiter" step proper.

Blind mode (default, ARBITER_BLIND_CRITIQUE=true):
  The critic receives each target response WITHOUT being told which model wrote
  it. This prevents social bias toward "prestige" models.

Non-blind mode (ARBITER_BLIND_CRITIQUE=false):
  The critic sees the full set of responses and can reference model names. Use
  for a meta-critique round where cross-referencing is valuable.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

from aethos_core.arbiter.models import CritiqueScore, ModelResponse
from aethos_core.config import get_settings

_log = logging.getLogger("aethos.arbiter.critique")

_CRITIQUE_TIMEOUT_SEC = 40.0

_CRITIQUE_SYSTEM = """\
You are an expert evaluator in a structured peer-review process.
You will receive a response written by another AI model and score it on three dimensions.

Respond ONLY with valid JSON in exactly this schema:
{
  "accuracy_score": <float 0.0-1.0>,
  "completeness_score": <float 0.0-1.0>,
  "reasoning_score": <float 0.0-1.0>,
  "recommended": <true|false>,
  "critique": "<1-3 sentence assessment>"
}

Scoring guide:
- accuracy_score: Is the content factually correct and free of hallucination?
- completeness_score: Does it fully address the prompt with appropriate depth?
- reasoning_score: Is the logic sound, well-structured, and free of fallacies?
- recommended: Would you recommend this response as the best answer?
- critique: Brief honest assessment. Note specific strengths and weaknesses.

Be rigorous. Do not inflate scores. Flag RLHF-style padding or false confidence.
"""


def _build_critique_prompt(
    original_prompt: str,
    target_response: ModelResponse,
    *,
    blind: bool = True,
    response_index: int = 0,
) -> str:
    label = f"Response {chr(65 + response_index)}" if blind else target_response.model_label
    return (
        f"Original prompt:\n{original_prompt}\n\n"
        f"---\n"
        f"{label}:\n{target_response.text}\n\n"
        f"---\n"
        f"Evaluate the response above."
    )


def _parse_critique_json(raw: str) -> dict[str, Any] | None:
    """Extract JSON from model output — handles markdown code fences."""
    clean = re.sub(r"```(?:json)?", "", raw, flags=re.I).strip().strip("`").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # Try to extract the first {...} block.
        m = re.search(r"\{.*\}", clean, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return None


def _failed_critique(critic_id: str, target_id: str, error: str) -> CritiqueScore:
    return CritiqueScore(
        critic_model_id=critic_id,
        target_response_id=target_id,
        accuracy_score=0.0,
        completeness_score=0.0,
        reasoning_score=0.0,
        overall_score=0.0,
        critique_text="",
        recommended=False,
        error=error,
    )


async def _critique_one(
    critic_entry: dict[str, str],
    original_prompt: str,
    target_response: ModelResponse,
    *,
    blind: bool,
    response_index: int,
    tenant_id: str | None = None,
) -> CritiqueScore:
    """One model critiques one target response."""
    # The critic uses the same dispatch path but with the critique system overlay
    # baked into the prompt body (the dispatch overlay is generic).
    from aethos_core.arbiter.dispatcher import _sync_complete

    prompt = _CRITIQUE_SYSTEM + "\n\n" + _build_critique_prompt(
        original_prompt, target_response, blind=blind, response_index=response_index
    )

    try:
        loop = asyncio.get_running_loop()
        raw_result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                _sync_complete,
                critic_entry["provider"],
                critic_entry["model_id"],
                prompt,
                tenant_id,
            ),
            timeout=_CRITIQUE_TIMEOUT_SEC,
        )
        parsed = _parse_critique_json(raw_result.get("text", ""))
        if not parsed:
            raise ValueError(f"Could not parse critique JSON from {critic_entry['model_id']}")

        def _clamp(v: Any) -> float:
            return max(0.0, min(1.0, float(v or 0)))

        accuracy = _clamp(parsed.get("accuracy_score", 0.5))
        completeness = _clamp(parsed.get("completeness_score", 0.5))
        reasoning = _clamp(parsed.get("reasoning_score", 0.5))
        overall = round((accuracy * 0.4 + completeness * 0.3 + reasoning * 0.3), 4)

        return CritiqueScore(
            critic_model_id=critic_entry["model_id"],
            target_response_id=target_response.response_id,
            accuracy_score=accuracy,
            completeness_score=completeness,
            reasoning_score=reasoning,
            overall_score=overall,
            critique_text=str(parsed.get("critique", ""))[:1000],
            recommended=bool(parsed.get("recommended", False)),
        )
    except asyncio.TimeoutError:
        return _failed_critique(
            critic_entry["model_id"],
            target_response.response_id,
            f"critique timeout after {_CRITIQUE_TIMEOUT_SEC}s",
        )
    except Exception as exc:
        return _failed_critique(
            critic_entry["model_id"], target_response.response_id, str(exc)
        )


async def run_critique_round(
    pool: list[dict[str, str]],
    original_prompt: str,
    responses: list[ModelResponse],
    *,
    blind: bool = True,
    tenant_id: str | None = None,
) -> list[CritiqueScore]:
    """
    Each model in the pool critiques every other model's response. A model does
    NOT critique its own response. Returns a flat list of CritiqueScore objects.
    """
    valid_responses = [r for r in responses if not r.error and r.text]
    if len(valid_responses) < 2:
        _log.warning("Critique round skipped: fewer than 2 valid responses.")
        return []

    # Build response_id → index map for blind labeling.
    resp_index = {r.response_id: i for i, r in enumerate(valid_responses)}

    tasks: list[asyncio.Task[CritiqueScore]] = []
    for critic_entry in pool:
        for resp in valid_responses:
            # Skip: a model does not critique itself.
            if critic_entry["model_id"] == resp.model_id:
                continue
            tasks.append(
                asyncio.ensure_future(
                    _critique_one(
                        critic_entry,
                        original_prompt,
                        resp,
                        blind=blind,
                        response_index=resp_index[resp.response_id],
                        tenant_id=tenant_id,
                    )
                )
            )

    if not tasks:
        return []

    s = get_settings()
    budget = float(getattr(s, "arbiter_timeout_sec", 180.0) or 180.0) * 0.35  # critique = 35%
    try:
        critiques = await asyncio.wait_for(asyncio.gather(*tasks), timeout=budget)
    except asyncio.TimeoutError:
        _log.warning("Critique round hit timeout at %.0fs", budget)
        critiques = []
        for task in tasks:
            if task.done() and not task.cancelled() and task.exception() is None:
                critiques.append(task.result())
            else:
                task.cancel()

    return list(critiques)
