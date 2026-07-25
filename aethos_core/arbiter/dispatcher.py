# SPDX-License-Identifier: Apache-2.0
"""
Parallel multi-model dispatcher — sends the same prompt to all pool models
simultaneously using asyncio.gather, collecting responses with per-model timeout.

This module ONLY calls the existing provider/completion.py infrastructure
(``_complete_one_attempt``). It does not modify provider routing, the model
catalog, or failover logic.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from aethos_core.arbiter.models import ModelResponse
from aethos_core.config import get_settings

_log = logging.getLogger("aethos.arbiter.dispatcher")

def _model_timeout_sec() -> float:
    from aethos_core.provider.completion import _provider_http_timeout, _provider_transient_retries

    # Budget for HTTP attempts + same-provider transient retries within one dispatch call,
    # but CAPPED: the arbiter fans out in parallel and a slow/stuck model should be dropped
    # (returned as an error response), not block the whole run for minutes. Without the cap
    # this was ~227s (http_timeout × retries), which made one slow model look like a hang.
    budget = _provider_http_timeout() * (1 + _provider_transient_retries()) + 2.0
    return max(45.0, min(budget, 75.0))


# System prompt injected for all arbiter dispatch calls. Tells the model it is
# one of several being evaluated in parallel.
_DISPATCH_SYSTEM = (
    "You are one of several AI models responding to the same prompt in parallel. "
    "Your response will be evaluated by the other models for accuracy, completeness, "
    "and reasoning quality. Be precise, evidence-based, and avoid padding. "
    "Do not claim certainty you do not have."
)


async def _call_one_model(
    entry: dict[str, str], prompt: str, *, tenant_id: str | None = None
) -> ModelResponse:
    """Call a single model asynchronously. Returns ModelResponse (error on failure)."""
    provider = entry["provider"]
    model_id = entry["model_id"]
    label = entry["label"]
    started = time.time()

    try:
        # Run the synchronous provider completion in a thread pool so we don't
        # block the event loop. The executor thread does NOT inherit the request
        # ContextVar, so we pass the owning tenant_id explicitly and re-establish
        # the tenant scope inside _sync_complete (Correction 1).
        loop = asyncio.get_running_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_complete, provider, model_id, prompt, tenant_id),
            timeout=_model_timeout_sec(),
        )
        latency_ms = int((time.time() - started) * 1000)
        return ModelResponse(
            response_id=(
                f"resp-{provider[:3]}-{model_id[:8].replace('/', '-')}-"
                f"{int(started * 1000) % 100000}"
            ),
            provider=provider,
            model_id=model_id,
            model_label=label,
            text=result.get("text", ""),
            input_tokens=result.get("input_tokens", 0),
            output_tokens=result.get("output_tokens", 0),
            latency_ms=latency_ms,
            used_llm=result.get("used_llm", True),
            error=result.get("error"),
        )
    except asyncio.TimeoutError:
        _log.warning(
            "Arbiter: model %s/%s timed out after %ss", provider, model_id, _model_timeout_sec()
        )
        return ModelResponse.error_response(
            provider, model_id, label, f"timeout after {_model_timeout_sec():.0f}s"
        )
    except Exception as exc:
        _log.exception("Arbiter: model %s/%s failed: %s", provider, model_id, exc)
        return ModelResponse.error_response(provider, model_id, label, str(exc))


def _sync_complete(
    provider: str, model_id: str, prompt: str, tenant_id: str | None = None
) -> dict[str, Any]:
    """
    Thin synchronous wrapper over existing provider/completion.py.
    Reuses ``_complete_one_attempt`` — no new HTTP logic added here.

    Runs in an executor thread with no request context, so it re-establishes the
    owning tenant from the stamped ``tenant_id`` (Correction 1) before any
    credential/config resolver runs.
    """
    from aethos_core.provider.completion import _complete_one_attempt
    from aethos_core.tenancy import tenant_scope

    with tenant_scope(tenant_id):
        result = _complete_one_attempt(
            prompt,
            provider=provider,
            model=model_id,
            include_identity=False,
            system_overlay=_DISPATCH_SYSTEM,
        )
    return {
        "text": result.text,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "used_llm": result.used_llm,
        "error": None if result.used_llm else result.text,
    }


async def dispatch_to_pool(
    pool: list[dict[str, str]],
    prompt: str,
    *,
    timeout_sec: float | None = None,
    tenant_id: str | None = None,
) -> list[ModelResponse]:
    """
    Dispatch prompt to all pool models in parallel.
    Returns responses in pool order (errors included — never raises).

    ``tenant_id`` is the owning arbiter session's stamped tenant; it is carried
    into each executor thread so detached fan-out resolves the right tenant.
    """
    s = get_settings()
    budget = timeout_sec or float(getattr(s, "arbiter_timeout_sec", 180.0) or 180.0)

    # Wrap coroutines in Tasks up front so we can inspect partial results if the
    # overall dispatch budget is exceeded.
    tasks = [
        asyncio.ensure_future(_call_one_model(entry, prompt, tenant_id=tenant_id)) for entry in pool
    ]
    try:
        responses = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=False),
            timeout=budget * 0.6,  # dispatch uses 60% of the total budget
        )
    except asyncio.TimeoutError:
        _log.warning(
            "Arbiter dispatch: overall timeout hit at %.0fs; collecting partial results",
            budget * 0.6,
        )
        responses = []
        for entry, task in zip(pool, tasks):
            if task.done() and not task.cancelled() and task.exception() is None:
                responses.append(task.result())
            else:
                task.cancel()
                responses.append(
                    ModelResponse.error_response(
                        entry["provider"], entry["model_id"], entry["label"], "session timeout"
                    )
                )

    return list(responses)
