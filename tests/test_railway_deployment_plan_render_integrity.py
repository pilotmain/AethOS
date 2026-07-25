# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 93B — Railway deployment plan survives finalization/cleanroom."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.route_trace import clear_route_traces_for_tests
from aethos_core.chat.service import ChatTurnResult, _finalize_result, resolve_chat_turn
from aethos_core.conversation.polish_compat import polish_chat_reply
from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import (
    render_railway_deployment_plan_artifact,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests,
    save_deployment_plan_context,
)

_REQUIRED = (
    "Railway target:",
    "Build/runtime:",
    "Required env vars:",
    "Governed execution plan:",
    "Risk:",
    "Rollback:",
    "Verification:",
    "No service has been created.",
)


def setup_function() -> None:
    clear_for_tests()
    clear_route_traces_for_tests()


def _plan_context() -> dict:
    return {
        "repo": "pilotmain/aethos",
        "branch": "main",
        "project": "pilotos",
        "environment": "production",
        "service_name": "aethos-api",
        "stage": "plan_draft",
        "mutation_ready": False,
    }


def _passed_checks() -> dict:
    return {
        "readonly_readiness_ok": True,
        "mutation_ready": False,
        "railway_credential_ok": True,
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {"ok": True},
        "github_binding": {"github_credential_ok": True},
        "service_creation": {},
    }


def test_casual_polish_truncates_without_bypass() -> None:
    raw = render_railway_deployment_plan_artifact(_plan_context(), checks=_passed_checks())
    polished = polish_chat_reply(reply=raw, intent="generative_answer", mode="casual")
    assert "Governed execution plan:" not in polished


def test_finalize_preserves_full_plan_with_relational_layer() -> None:
    raw = render_railway_deployment_plan_artifact(_plan_context(), checks=_passed_checks())
    emotional = {
        "mode": {"mode": "executive"},
        "signals": {"frustrated": True, "signals": ["frustrated"]},
        "session_id": "render-93b",
        "channel": "chat",
    }
    out = _finalize_result(
        ChatTurnResult(
            reply=raw,
            intent="railway_deployment_plan_draft",
            meta={
                "route_id": "railway_deployment_plan",
                "presentation_bypass": "true",
                "suppress_governance_footer": "true",
            },
        ),
        emotional_context=emotional,
    )
    for section in _REQUIRED:
        assert section in out.reply, section


@patch("aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options")
@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_create_plan_full_output_live_path(mock_checks, mock_options) -> None:
    mock_checks.return_value = _passed_checks()
    mock_options.return_value = []
    result = resolve_chat_turn(
        "create railway deployment plan for pilotmain/aethos in pilotos / production",
        session_id="render-93b-create",
        apply_relational_layer=True,
    )
    assert result.intent == "railway_deployment_plan_draft"
    for section in _REQUIRED:
        assert section in result.reply, section


@patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks")
def test_show_plan_full_output_live_path(mock_checks) -> None:
    mock_checks.return_value = _passed_checks()
    save_deployment_plan_context(session_id="render-93b-show", plan=_plan_context())
    result = resolve_chat_turn(
        "show railway deployment plan",
        session_id="render-93b-show",
        apply_relational_layer=True,
    )
    assert result.intent == "railway_deployment_plan_show"
    for section in _REQUIRED:
        assert section in result.reply, section
