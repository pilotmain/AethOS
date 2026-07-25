# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.intents import (
    extract_target_hints,
    infer_operation_preflight_intent,
    matches_vercel_failure_diagnostic,
)


FAILURE_PROMPTS = [
    "why did talking-avatar-agent fail",
    "why is quotepilot failing",
    "why did latest deploy fail",
    "what failed in lifeos",
    "why did deployment fail",
    "why is deployment failing",
    "why did app break for talking-avatar-agent",
]


def test_failure_phrases_match_diagnostic_matcher():
    for prompt in FAILURE_PROMPTS:
        assert matches_vercel_failure_diagnostic(prompt), prompt


def test_failure_phrases_route_to_vercel_down_preflight():
    for prompt in FAILURE_PROMPTS:
        out = infer_operation_preflight_intent(prompt)
        assert out is None, prompt


def test_failure_phrases_extract_project_hints():
    assert "talking-avatar-agent" in extract_target_hints("why did talking-avatar-agent fail")
    assert "quotepilot" in extract_target_hints("why is quotepilot failing")
    assert "lifeos" in extract_target_hints("what failed in lifeos")


def test_latest_deploy_failure_has_no_project_hint():
    hints = extract_target_hints("why did latest deploy fail")
    assert "latest" not in hints
    assert "deploy" not in hints
