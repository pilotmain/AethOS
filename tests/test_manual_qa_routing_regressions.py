# SPDX-License-Identifier: Apache-2.0
"""Regressions found in the 2026-06-18 manual QA pass.

1. "Render a table comparing X vs Y" was hijacked by the Render.com provider lane
   instead of drawing a table on the Canvas (canvas detector missed artifact nouns
   like "table" and required the literal word "canvas").
2. "Deploy ... to Railway" produced a Vercel preflight (deploy_from_git branch
   ignored an explicit Railway target).
3. "Switch model" was answered with ".env + restart" guidance; model selection is
   the in-chat picker, so the agent's truth block must say so.
"""

from __future__ import annotations

import pytest

from aethos_core.chat.front_door_intent import is_canvas_render_request
from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.mission_control.visible_navigation_registry import render_capability_truth_lines


@pytest.mark.parametrize(
    "prompt",
    [
        "Render a table comparing Postgres vs SQLite for our identity store: columns durability, concurrency, ops cost",
        "draw a comparison of Vercel vs Cloudflare",
        "render a diff of the railway env",
        "visualize a dashboard of job health",
    ],
)
def test_canvas_render_recognized_for_artifact_nouns(prompt):
    assert is_canvas_render_request(prompt) is True


@pytest.mark.parametrize(
    "prompt",
    [
        "deploy my repo to Railway",
        "restart the aethos-api service",
        "show me the latest deployment logs",
        "list my vercel deployments",
        "render the production service status from railway logs",
    ],
)
def test_canvas_render_does_not_hijack_operational(prompt):
    assert is_canvas_render_request(prompt) is False


def _provider(result):
    return result[2].get("provider") if result and len(result) > 2 and isinstance(result[2], dict) else None


def test_deploy_from_git_honors_explicit_railway_target():
    assert _provider(infer_operation_preflight_intent("Deploy a repo called foo-123 to Railway")) == "railway"


def test_deploy_from_git_defaults_to_vercel_when_unspecified():
    assert _provider(infer_operation_preflight_intent("Deploy my-app from git to Vercel")) == "vercel"


def test_model_switch_guidance_points_to_picker_not_env():
    block = "\n".join(render_capability_truth_lines()).lower()
    assert "model selector" in block
    assert "switching the chat model" in block
    # The model-switch line must not tell users to edit .env / restart for model changes.
    import re
    model_line = [ln for ln in render_capability_truth_lines() if "switching the chat model" in ln.lower()][0]
    assert "never tell the user to edit .env or restart" in model_line.lower()
