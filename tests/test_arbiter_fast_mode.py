# SPDX-License-Identifier: Apache-2.0
"""Arbiter fast mode: skip the peer-critique round for a quicker result (parallel answers,
no cross-ranking). The expensive phase is critique, so this is the main latency lever."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from aethos_core.arbiter import service
from aethos_core.arbiter.models import ModelResponse

_POOL = [
    {"provider": "anthropic", "model_id": "claude-x", "label": "Claude"},
    {"provider": "openrouter", "model_id": "openai/gpt-4o-mini", "label": "GPT-4o mini"},
]


async def _fake_dispatch(pool, prompt, *, tenant_id=None):
    return [
        ModelResponse(response_id="r1", provider="anthropic", model_id="claude-x", model_label="Claude", text="A"),
        ModelResponse(response_id="r2", provider="openrouter", model_id="openai/gpt-4o-mini", model_label="GPT", text="B"),
    ]


def _run(fast: bool):
    crit = AsyncMock(return_value=[])
    with patch("aethos_core.arbiter.service.dispatch_to_pool", _fake_dispatch), \
         patch("aethos_core.arbiter.service.run_critique_round", crit), \
         patch("aethos_core.arbiter.service.validate_pool", return_value={"valid": True, "errors": []}), \
         patch("aethos_core.arbiter.service.effective_bool", return_value=True):
        sess = asyncio.run(service.run_arbiter_session("q", model_pool_override=_POOL, fast=fast))
    return sess, crit


def test_fast_mode_skips_critique():
    sess, crit = _run(fast=True)
    crit.assert_not_called()
    assert sess.critiques == []
    assert sess.rounds_completed == 1  # dispatch only
    assert sess.consensus is not None  # still produces a consensus result


def test_full_mode_runs_critique():
    sess, crit = _run(fast=False)
    crit.assert_called_once()
    assert sess.rounds_completed == 2  # dispatch + critique
