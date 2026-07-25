# SPDX-License-Identifier: Apache-2.0
"""External research must not be hijacked by provider-inventory / operational-cognition lanes."""

from __future__ import annotations

import pytest

from aethos_core.chat.chat_turn_steps import is_external_research_request


@pytest.mark.parametrize(
    "prompt",
    [
        "research the tradeoffs of deploying a Next.js 14 app on Railway vs Vercel and cite sources",
        "research Plaid production access requirements and summarize the steps",
        "look up the latest Next.js 14 caching docs",
        "search the web for Stripe webhook best practices",
    ],
)
def test_external_research_detected(prompt):
    assert is_external_research_request(prompt) is True


@pytest.mark.parametrize(
    "prompt",
    [
        "compare the two failed deployments",
        "show my Railway services",
        "render a diff on the canvas",
        "what's blocking the killit deploy?",
    ],
)
def test_operational_not_treated_as_research(prompt):
    assert is_external_research_request(prompt) is False
