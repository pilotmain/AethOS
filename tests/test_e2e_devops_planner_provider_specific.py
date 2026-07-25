# SPDX-License-Identifier: Apache-2.0
"""Provider-specific E2E DevOps planner tests."""

from __future__ import annotations

from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply
from aethos_core.devops_intent_planner.end_to_end_plan_builder import compose_end_to_end_plan_reply
from aethos_core.devops_intent_planner.provider_specific_plan_builder import compose_provider_specific_e2e_plan_reply


def test_provider_specific_plan_has_ten_steps() -> None:
    prompt = "can you push to github, deploy to vercel, create env vars, and check E2E?"
    reply = compose_provider_specific_e2e_plan_reply(prompt, session_id="fix58-plan")
    assert "Provider-specific end-to-end workflow:" in reply
    assert "Identify the local repo path" in reply
    assert "Verify GitHub checks" in reply
    assert "Verify deployment health" in reply
    assert reply.index("10.") < len(reply)
    assert "No mutation has been performed." in reply


def test_provider_specific_plan_uses_github_label_not_github_title() -> None:
    prompt = "can you push to github and deploy?"
    reply = compose_end_to_end_plan_reply(prompt, session_id="fix58-label")
    assert "GitHub" in reply
    assert "Github" not in reply


def test_provider_specific_plan_lists_expansion_status() -> None:
    prompt = "push to github, deploy on vercel, set env vars"
    reply = compose_end_to_end_plan_reply(prompt, session_id="fix58-expansion")
    assert "GitHub wired now:" in reply
    assert "Vercel wired now:" in reply
    assert "expanding next:" in reply


def test_provider_specific_plan_blocks_premature_preflight() -> None:
    prompt = "can you push to github, deploy, create env vars, and check E2E?"
    assert create_mutation_preflight_job_reply(prompt, session_id="fix58-no-preflight") is None


def test_provider_specific_plan_prioritizes_github_then_vercel() -> None:
    reply = compose_provider_specific_e2e_plan_reply(
        "push to github and deploy to vercel",
        session_id="fix58-priority",
    )
    assert "deepen **GitHub** first, then **Vercel**" in reply
