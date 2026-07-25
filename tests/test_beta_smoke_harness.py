# SPDX-License-Identifier: Apache-2.0
"""Beta smoke harness — one runner, one test name per locked capability (program §4–§5).

Run the locking gate:
    pytest tests -q -k beta_smoke

Stages listed in LOCKED_BETA_SMOKE_STAGES must stay green on every change.
Add a stage only after Fix → Harden → Lock for that capability.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from aethos_core.canvas.canvas_store import clear_canvas_for_tests, get_canvas_state
from aethos_core.canvas.session_context import clear_canvas_client_session_for_tests
from aethos_core.channels.channel_registry import compose_channel_health_reply, is_channel_health_request
from aethos_core.chat.chat_turn_steps import try_single_loop_turn
from aethos_core.chat.explicit_mutation_intent import compose_explicit_mutation_preflight_reply
from aethos_core.chat.provider_read_intent import compose_provider_read_inventory_reply, contains_deflection_runaround
from aethos_core.config import get_settings
from aethos_core.conversation.progression_compat import append_optional_rest_hint, reset_rest_nudge_state_for_tests
from aethos_core.identity.onboarding_capability_intro import (
    LOCKED_BETA_SMOKE_STAGE_IDS,
    onboarding_capability_bullets,
)
from aethos_core.memory.conversation_summary_memory import record_turn, reset_for_tests as reset_conversation_memory

LOCKED_BETA_SMOKE_STAGES: tuple[str, ...] = LOCKED_BETA_SMOKE_STAGE_IDS


def beta_smoke_locked_stages() -> tuple[str, ...]:
    return LOCKED_BETA_SMOKE_STAGES


@pytest.fixture(autouse=True)
def _clear_canvas_and_memory(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "canvas_store_dir", str(tmp_path / "canvas_smoke"))
    monkeypatch.setattr(get_settings(), "canvas_surface_enabled", True)
    monkeypatch.setattr(get_settings(), "conversation_memory_dir", str(tmp_path / "conv_mem"))
    get_settings.cache_clear()
    reset_conversation_memory()
    reset_rest_nudge_state_for_tests()
    clear_canvas_for_tests()
    clear_canvas_client_session_for_tests()
    yield
    reset_conversation_memory()
    reset_rest_nudge_state_for_tests()
    clear_canvas_for_tests()
    clear_canvas_client_session_for_tests()
    get_settings.cache_clear()


def test_beta_smoke_registry_lists_locked_stages():
    assert "foundation_single_loop" in LOCKED_BETA_SMOKE_STAGES
    assert len(LOCKED_BETA_SMOKE_STAGES) >= 11
    assert len(onboarding_capability_bullets()) == len(LOCKED_BETA_SMOKE_STAGES)


def test_beta_smoke_foundation_single_loop_enabled():
    assert get_settings().chat_single_loop_enabled is True


def test_beta_smoke_foundation_responding_not_mutation_target():
    """Regression: plain 'why aren't you responding' must not become a deploy target."""
    with patch("aethos_core.chat.explicit_mutation_intent.compose_explicit_mutation_preflight_reply", return_value=None):
        with patch(
            "aethos_core.chat.provider_read_intent.compose_provider_read_inventory_reply",
            return_value=None,
        ):
            with patch(
                "aethos_core.chat.provider_read_intent.compose_provider_health_followup_reply",
                return_value=None,
            ):
                with patch("aethos_core.provider.completion.complete_chat") as mock_chat:
                    mock_chat.return_value = type(
                        "Prov",
                        (),
                        {"text": "I'm here — what should we work on?", "used_llm": True, "provider": "test", "model": "test"},
                    )()
                    result = try_single_loop_turn(
                        "why aren't you responding",
                        session_id="sess-beta-smoke-responding",
                        channel="chat",
                        surface="webchat",
                    )
    assert result is not None
    reply = (result.reply or "").lower()
    assert "deployment target" not in reply
    assert "register" not in reply or "responding" not in reply


def test_beta_smoke_chat_basic_qa_summarize_url():
    from aethos_core.research.research_provider import WebsiteSummary

    summary = WebsiteSummary(
        ok=True,
        url="https://pilotmain.com",
        title="PilotMain",
        meta_description="AI operations platform.",
        visible_text_preview="# pilotmain.com\n\nPilotMain is an AI operations platform.",
        artifact_ids=["art-1"],
        confidence="high",
    )
    with patch(
        "aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn",
    ) as mock_agent:
        from aethos_core.execution_brain.agent_runtime import AgentRuntimeResult

        mock_agent.return_value = AgentRuntimeResult(
            reply=summary.visible_text_preview,
            used_llm=True,
            meta={"lane": "agent_runtime", "suppress_governance_footer": "true"},
        )
        result = try_single_loop_turn(
            "summarize pilotmain.com",
            session_id="sess-beta-smoke-qa-sum",
            channel="chat",
            surface="webchat",
        )
    assert result is not None
    assert "pilotmain" in (result.reply or "").lower()
    assert "informational_help" not in (result.intent or "")
    assert not contains_deflection_runaround(result.reply or "")


def test_beta_smoke_chat_basic_qa_expand_uses_memory():
    session_id = "sess-beta-smoke-qa-expand"
    record_turn(
        session_id=session_id,
        user_text="summarize pilotmain.com",
        reply="PilotMain is a governed AI operations platform for teams.",
        intent="agent_runtime",
    )
    expanded = (
        "PilotMain is your operator cockpit: governed mutations, provider inventory, "
        "and chat-first control across Railway, Vercel, and GitHub."
    )
    with patch(
        "aethos_core.execution_brain.agent_runtime.run_agent_runtime_turn",
    ) as mock_agent:
        from aethos_core.execution_brain.agent_runtime import AgentRuntimeResult

        mock_agent.return_value = AgentRuntimeResult(
            reply=expanded,
            used_llm=True,
            meta={"lane": "agent_runtime", "suppress_governance_footer": "true"},
        )
        result = try_single_loop_turn(
            "now expand it",
            session_id=session_id,
            channel="chat",
            surface="webchat",
        )
    assert result is not None
    reply = (result.reply or "").lower()
    assert "pilotmain" in reply or "governed" in reply
    assert "what do you want to summarize" not in reply


def test_beta_smoke_chat_basic_qa_rest_nudge_at_most_once():
    session_id = "sess-beta-smoke-qa-nudge"
    hits = 0
    for _ in range(20):
        out = append_optional_rest_hint("ok", session_id=session_id)
        if "rest" in out.lower() or "sleep" in out.lower():
            hits += 1
    assert hits <= 1


def test_beta_smoke_canvas_structured_render_operator_session_tool_gate():
    """Canvas must work through the tool policy for realistic web session ids (sess-…)."""
    from aethos_core.execution_brain.agent_tool_executor import execute_agent_tool
    from aethos_core.execution_brain.agent_tool_policy import is_tool_allowed

    session_id = "sess-d5di5px5"
    assert is_tool_allowed(
        "canvas_render",
        channel="chat",
        session_id=session_id,
        surface="webchat",
    )
    out = execute_agent_tool(
        "canvas_render",
        {
            "view_type": "job_timeline",
            "title": "Jobs",
            "data": {"events": [{"label": "Preflight", "status": "completed"}]},
        },
        session_id=session_id,
        channel="chat",
        surface="webchat",
    )
    payload = json.loads(out)
    assert payload.get("ok") is True
    state = get_canvas_state(session_id=session_id)
    assert state["view_count"] == 1
    assert state["views"][0]["view_type"] == "job_timeline"


def test_beta_smoke_canvas_sandboxed_subagent_still_denied():
    from aethos_core.execution_brain.agent_tool_policy import is_tool_allowed

    assert not is_tool_allowed(
        "canvas_render",
        channel="chat",
        session_id="agent:sess-parent:subagent:spawn-1",
        surface="webchat",
    )


def test_beta_smoke_telegram_test_send_propagates_detail():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
        with patch(
            "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
            return_value=("bot-token", "cred-1"),
        ):
            with patch(
                "aethos_core.channels.telegram.telegram_transport.send_telegram_message",
                return_value={"ok": False, "detail": "Bad Request: chat not found"},
            ):
                with TestClient(app) as client:
                    r = client.post(
                        "/api/v1/channels/telegram/test-send",
                        json={"chat_id": "999", "message": "hi"},
                    )
    assert r.status_code == 502
    body = r.json()
    assert body.get("detail") == "Bad Request: chat not found"
    assert "test_send_failed" not in str(body.get("detail") or "")


def test_beta_smoke_telegram_production_webhook_verified():
    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    canonical = "https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook"
    with patch("aethos_core.production.deployment_mode.telegram_canonical_webhook_url", return_value=canonical):
        with patch(
            "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
            return_value=("bot-token", "cred-1"),
        ) as mock_resolve:
            with patch(
                "aethos_core.channels.telegram.telegram_transport.set_webhook",
                return_value={"ok": True, "detail": "Webhook configured"},
            ):
                with patch(
                    "aethos_core.channels.telegram.telegram_transport.get_webhook_info",
                    return_value={"ok": True, "url": canonical},
                ):
                    with TestClient(app) as client:
                        r = client.post("/api/v1/channels/telegram/webhook/register/production")
    mock_resolve.assert_called()
    body = r.json()
    assert body["ok"] is True
    assert body.get("verified") is True
    assert body["webhook_url"] == canonical


def test_beta_smoke_telegram_register_uses_request_tenant_scope():
    from aethos_core.tenancy import get_current_tenant

    seen: list[str] = []

    def _resolve():
        seen.append(get_current_tenant())
        return "bot-token", "cred-1"

    with patch(
        "aethos_core.channels.telegram.telegram_token.resolve_telegram_bot_token",
        side_effect=_resolve,
    ):
        from aethos_core.api.routes.telegram import register_telegram_webhook_production_api

        class _Req:
            state = type("S", (), {"user": {"user_id": "tenant-alpha"}})()

        with patch(
            "aethos_core.production.deployment_mode.telegram_canonical_webhook_url",
            return_value="https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook",
        ):
            with patch(
                "aethos_core.channels.telegram.telegram_transport.set_webhook",
                return_value={"ok": True, "detail": "ok"},
            ):
                with patch(
                    "aethos_core.channels.telegram.telegram_transport.get_webhook_info",
                    return_value={"ok": True, "url": "https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook"},
                ):
                    with patch("aethos_core.config.get_settings") as mock_settings:
                        mock_settings.return_value.multi_tenant_enabled = True
                        register_telegram_webhook_production_api(_Req())
    assert seen == ["tenant-alpha"]


def test_beta_smoke_channel_health_routing_telegram():
    assert is_channel_health_request("what's wrong with telegram?")
    status = {
        "token_configured": True,
        "token_source": "vault",
        "transport_health": "ok",
        "channel_gateway_enabled": True,
        "expected_webhook_url": "https://pilotmain.com/aethos-api/api/v1/channels/telegram/webhook",
        "webhook_mismatch": True,
        "webhook": {"url": "https://stale.ngrok-free.dev/webhook"},
        "last_received_at": None,
        "last_sent_at": None,
        "last_send_ok": False,
        "last_send_error": "Bad Request: chat not found",
    }
    with patch(
        "aethos_core.channels.telegram.telegram_runtime.telegram_channel_status",
        return_value=status,
    ):
        out = compose_channel_health_reply("investigate why telegram is failing")
    assert out is not None
    body, intent, meta = out
    assert intent == "telegram_channel_health"
    assert "Register production webhook" in body
    assert "local workspace" not in body.lower()
    assert meta.get("lane") == "channel_health"


def test_beta_smoke_railway_readonly_direct_no_preflight_job():
    from aethos_core.chat.railway_readonly_prompts import create_railway_readonly_job_reply
    from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal
    from aethos_core.operational_session.railway_readonly_executor import ReadonlyExecutionResult
    from aethos_core.operational_session.session_subject import SessionSubject

    with patch(
        "aethos_core.chat.railway_readonly_prompts.resolve_railway_auth_for_chat",
        return_value={"credential_id": "cred-r", "block_reason": None},
    ):
        with patch(
            "aethos_core.operational_session.active_subject_resolver.resolve_active_subject",
        ) as mock_subject:
            mock_subject.return_value.subject = SessionSubject(provider="railway", subject_source="session")
            with patch(
                "aethos_core.operational_session.operational_readonly_goal.classify_readonly_goal",
                return_value=ReadonlyGoal(operation="deployment_status", user_text="check railway deployment"),
            ):
                with patch(
                    "aethos_core.operational_session.railway_readonly_executor.execute_railway_readonly",
                    return_value=ReadonlyExecutionResult(
                        ok=True,
                        reply="**Railway deployment status:**\n\n- aethos-api — healthy",
                        operation="deployment_status",
                    ),
                ):
                    with patch(
                        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
                        return_value={"required_env_vars": ["RAILWAY_API_TOKEN (validated)"]},
                    ):
                        out = create_railway_readonly_job_reply(
                            "check my Railway deployment and env",
                            session_id="sess-beta-smoke-rail",
                        )
    assert out is not None
    body, intent, meta = out
    assert intent == "railway_readonly_direct"
    assert meta.get("route_id") == "railway_readonly_direct"
    assert "Created tracked preflight" not in body


def _mock_inventory(provider: str) -> dict:
    if provider == "railway":
        return {
            "ok": True,
            "inventory": {
                "projects": [
                    {
                        "name": "aethos-prod",
                        "environments": [
                            {
                                "name": "production",
                                "services": [
                                    {
                                        "name": "api",
                                        "service_type": "web",
                                        "status": "running",
                                        "health": "healthy",
                                        "deployment_state": "SUCCESS",
                                        "deployment_url": "api.up.railway.app",
                                    },
                                    {
                                        "name": "worker",
                                        "service_type": "worker",
                                        "status": "crashed",
                                        "health": "failed",
                                        "deployment_state": "FAILED",
                                        "deployment_url": "",
                                    },
                                ],
                            }
                        ],
                    }
                ],
            },
        }
    return {
        "ok": True,
        "inventory": {
            "project_count": 2,
            "projects": [
                {
                    "name": "aethos-web",
                    "latest_production_state": "ready",
                    "production_url": "https://aethos-web.vercel.app",
                },
                {
                    "name": "aethos-api",
                    "latest_production_state": "error",
                    "production_url": "https://aethos-api.vercel.app",
                },
            ],
        },
    }


def test_beta_smoke_provider_inventory_health_railway_and_vercel():
    for provider, prompt in (
        ("railway", "list my railway projects and health"),
        ("vercel", "show vercel projects health status"),
    ):
        with patch(
            "aethos_core.execution_brain.provider_agent_ops.provider_inventory",
            return_value=_mock_inventory(provider),
        ):
            out = compose_provider_read_inventory_reply(prompt, session_id=f"sess-beta-smoke-{provider}")
        assert out is not None
        body, intent, meta = out
        assert intent == "provider_read_inventory"
        assert "healthy" in body.lower() or "failed" in body.lower()
        assert "unknown" not in body.lower() or "healthy" in body.lower()
        assert not contains_deflection_runaround(body)
        assert meta.get("provider") == provider


def test_beta_smoke_repo_analysis_github_remote():
    report = (
        "# GitHub repo analysis — `pilotmain/aethos`\n\n"
        "## Stack & manifests\n\n- **Detected:** Python\n\n"
        "_Read via GitHub API (no local workspace registration required on hosted)._"
    )
    with patch(
        "aethos_core.providers.github.operations.repo_remote_read_api.analyze_github_repo_for_chat",
        return_value={
            "ok": True,
            "report": report,
            "snapshot": {"ok": True, "repository": "pilotmain/aethos"},
        },
    ):
        result = try_single_loop_turn(
            "analyze pilotmain/aethos",
            session_id="sess-beta-smoke-repo",
            channel="chat",
            surface="webchat",
        )
    assert result is not None
    assert result.intent == "github_remote_analysis"
    assert "pilotmain/aethos" in (result.reply or "")
    assert "register local" not in (result.reply or "").lower()


def test_beta_smoke_arbiter_consensus_two_providers():
    from aethos_core.execution_brain.agent_tool_executor import _execute_arbiter_run

    pool = [
        {"provider": "anthropic", "model_id": "claude-sonnet-4-6", "label": "anthropic/claude"},
        {"provider": "openrouter", "model_id": "openai/gpt-4.1", "label": "openrouter/gpt"},
    ]
    with patch("aethos_core.config.get_settings") as mock_settings:
        mock_settings.return_value.arbiter_enabled = True
        with patch("aethos_core.arbiter.pool.parse_model_pool", return_value=pool):
            with patch("aethos_core.arbiter.pool.validate_pool", return_value={"valid": True, "errors": []}):
                with patch(
                    "aethos_core.execution_brain.agent_tool_executor._run_arbiter_session_sync",
                ) as mock_run:
                    from aethos_core.arbiter.models import ArbiterSession, ArbiterStatus, ConsensusResult

                    mock_run.return_value = ArbiterSession(
                        session_id="arb-1",
                        status=ArbiterStatus.COMPLETED,
                        model_pool=pool,
                        responses=[],
                        consensus=ConsensusResult(
                            winning_response_id="r1",
                            winning_model_id="anthropic:claude",
                            winning_model_label="anthropic/claude",
                            winning_text="Agreed approach",
                            agreement_score=0.9,
                            consensus_reached=True,
                            consensus_threshold=0.7,
                            total_models=2,
                            responding_models=2,
                            agreeing_models=2,
                            dissenting_model_ids=[],
                            round_count=1,
                            summary="Models agree on the approach.",
                        ),
                    )
                    payload = json.loads(
                        _execute_arbiter_run({"prompt": "compare deploy strategies"}, session_id="sess-arb")
                    )
    assert payload.get("ok") is True
    assert payload.get("model_count") == 2


def test_beta_smoke_arbiter_consensus_single_provider_honest():
    from aethos_core.execution_brain.agent_tool_executor import _execute_arbiter_run

    pool = [{"provider": "anthropic", "model_id": "claude-sonnet-4-6", "label": "anthropic/claude"}]
    with patch("aethos_core.config.get_settings") as mock_settings:
        mock_settings.return_value.arbiter_enabled = True
        with patch("aethos_core.arbiter.pool.parse_model_pool", return_value=pool):
            with patch(
                "aethos_core.arbiter.pool.validate_pool",
                return_value={
                    "valid": False,
                    "errors": ["Arbiter requires at least 2 models from your enabled pool; got 1."],
                },
            ):
                payload = json.loads(
                    _execute_arbiter_run({"prompt": "compare deploy strategies"}, session_id="sess-arb-1")
                )
    assert payload.get("ok") is False
    assert payload.get("error") == "pool_insufficient"
    assert "2 models" in str(payload.get("hint") or "").lower()


def test_beta_smoke_deploy_end_to_end_readiness_direct():
    readiness_body = (
        "**Railway deployment readiness**\n\n"
        "- GitHub credential: ok\n"
        "- Railway API: ok\n"
        "- Missing: SERVICE_PORT env var"
    )
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_router.route_railway_deployment_readiness",
        return_value=(readiness_body, "railway_deployment_readiness", {"lane": "deployment_readiness", "read_only": "true"}),
    ):
        result = try_single_loop_turn(
            "run railway deployment readiness checks",
            session_id="sess-beta-smoke-deploy-read",
            channel="chat",
            surface="webchat",
        )
    assert result is not None
    assert "readiness" in (result.reply or "").lower() or "railway" in (result.reply or "").lower()
    assert "Created tracked preflight" not in (result.reply or "")
    assert result.meta.get("single_loop") == "true"


def test_beta_smoke_deploy_end_to_end_mutation_preflight_railway():
    from aethos_core.execution_brain.agent_tool_policy import is_tool_allowed

    operator_session = "sess-deploy-e2e"
    assert is_tool_allowed(
        "provider_create_mutation_preflight",
        channel="chat",
        session_id=operator_session,
        surface="webchat",
    )
    assert not is_tool_allowed(
        "provider_create_mutation_preflight",
        channel="telegram",
        session_id=operator_session,
        surface="webchat",
    )

    with patch(
        "aethos_core.chat.mutation_preflight_prompts.create_mutation_preflight_job_reply",
        return_value=(
            "Created tracked preflight for Railway redeploy.",
            "mutation_preflight",
            {"provider": "railway", "operation_type": "redeploy", "lane": "mutation_preflight"},
        ),
    ):
        out = compose_explicit_mutation_preflight_reply(
            "redeploy killit on railway",
            session_id=operator_session,
        )
    assert out is not None
    body, intent, meta = out
    assert meta.get("provider") == "railway" or "railway" in body.lower()
    assert intent == "mutation_preflight"


def test_beta_smoke_engineering_review_connected_repo():
    report = (
        "# GitHub repo analysis — `pilotmain/aethos`\n\n"
        "## CI / workflows\n\n- `.github/workflows/ci.yml`\n\n"
        "## Enhancement opportunities\n\n- package.json lists dependencies"
    )
    with patch(
        "aethos_core.providers.github.operations.repo_remote_read_api.analyze_github_repo_for_chat",
        return_value={
            "ok": True,
            "report": report,
            "snapshot": {"ok": True, "repository": "pilotmain/aethos", "workflows": [".github/workflows/ci.yml"]},
        },
    ):
        result = try_single_loop_turn(
            "scan workflows and dependency risks for pilotmain/aethos",
            session_id="sess-beta-smoke-eng",
            channel="chat",
            surface="webchat",
        )
    assert result is not None
    assert result.intent in {"workflow_analysis", "dependency_audit", "github_remote_analysis", "architecture_analysis"}
    assert "ci" in (result.reply or "").lower() or "workflow" in (result.reply or "").lower()
    assert "register local repo" not in (result.reply or "").lower()


def test_beta_smoke_model_selection_and_failover(monkeypatch):
    """Locked stage: honor selection, cross-provider failover, honest all-fail errors."""
    from aethos_core.llm.effective_model import EffectiveModel
    from aethos_core.provider import completion as completion_mod
    from aethos_core.provider.completion import ToolLoopResult, run_tool_loop_with_provider_failover

    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
    monkeypatch.setenv("MODEL_FAILOVER_ENABLED", "true")
    get_settings.cache_clear()

    effective = EffectiveModel(
        catalog_id="anthropic:claude-opus-4-6",
        provider="anthropic",
        model="claude-opus-4-6",
        label="Claude Opus 4.6",
        source="session",
    )
    calls: list[tuple[str, str]] = []

    def _record_attempt(provider: str, model: str, **kwargs):
        calls.append((provider, model))
        if provider == "anthropic":
            return ToolLoopResult(
                text="Anthropic returned 404 (model not found for your API key)",
                provider="anthropic",
                model=model,
                used_llm=False,
                loop_outcome="error_degraded",
            )
        return ToolLoopResult(
            text="answer from failover provider",
            provider=provider,
            model=model,
            used_llm=True,
            tool_calls=1,
            iterations=1,
        )

    with patch.object(completion_mod, "_run_tool_loop_one_attempt", side_effect=_record_attempt):
        result = run_tool_loop_with_provider_failover(
            effective,
            system="sys",
            user_message="hello",
            tools=[],
            tool_executor=lambda _n, _i: "",
            max_iterations=2,
            max_tool_streak=5,
            channel="chat",
        )

    assert calls[0] == ("anthropic", "claude-opus-4-6")
    assert result is not None
    assert result.used_llm is True
    assert result.provider != "anthropic"
    assert "continued on" in result.text

    calls.clear()
    def _always_fail(provider: str, model: str, **kwargs):
        calls.append((provider, model))
        return ToolLoopResult(
            text=f"{provider} auth failed",
            provider=provider,
            model=model,
            used_llm=False,
            loop_outcome="error_degraded",
        )

    with patch.object(completion_mod, "_run_tool_loop_one_attempt", side_effect=_always_fail):
        all_fail = run_tool_loop_with_provider_failover(
            effective,
            system="sys",
            user_message="hello",
            tools=[],
            tool_executor=lambda _n, _i: "",
            max_iterations=2,
            max_tool_streak=5,
            channel="chat",
        )

    assert all_fail is not None
    assert "All configured providers failed" in all_fail.text
    assert "Claude Opus 4.6" in all_fail.text or "auth failed" in all_fail.text


def test_beta_smoke_model_selection_honored_for_tool_loop(monkeypatch):
    from aethos_core.llm.effective_model import (
        effective_model_for_agent_tool_loop,
        resolve_effective_model,
    )
    from aethos_core.llm.session_model_override import set_session_model_override

    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
    get_settings.cache_clear()

    sid = "beta-smoke-model-honored"
    set_session_model_override(sid, "anthropic:claude-opus-4-6")
    effective = resolve_effective_model(session_id=sid)
    tool_model = effective_model_for_agent_tool_loop(effective)
    assert tool_model is not None
    assert tool_model.catalog_id == effective.catalog_id
    assert tool_model.model == "claude-opus-4-6"


def test_beta_smoke_tenant_owner_can_approve(monkeypatch):
    from aethos_core.security import rbac

    monkeypatch.delenv("PLATFORM_OWNER_EMAILS", raising=False)
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    get_settings.cache_clear()

    jeremy = {"user_id": "jeremy@example.com", "email": "jeremy@example.com", "roles": ["tenant_admin"]}
    existing_op = {"user_id": "operator@example.com", "email": "operator@example.com", "roles": ["operator"]}
    approve_path = "/api/v1/channels/pairing/approve"

    assert rbac.is_tenant_owner(jeremy)
    jeremy_perms = rbac.permissions_for_user(jeremy)
    assert rbac.APPROVE in jeremy_perms
    assert rbac.MANAGE_USERS not in jeremy_perms
    assert rbac.is_authorized(["tenant_admin"], "POST", approve_path, user=jeremy)

    assert rbac.is_tenant_owner(existing_op)
    assert rbac.APPROVE in rbac.permissions_for_user(existing_op)
    assert rbac.is_authorized(["operator"], "POST", approve_path, user=existing_op)


def test_beta_smoke_deploy_routes_to_deploy(monkeypatch):
    from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent
    from aethos_core.chat.railway_readonly_prompts import is_railway_readonly_direct_request

    deploy_text = "deploy killit to railway and set up the env vars"
    assert not is_railway_readonly_direct_request(deploy_text)
    intent = detect_explicit_mutation_intent(deploy_text)
    assert intent is not None
    assert intent.operation == "deploy"
    assert intent.provider == "railway"
    assert "killit" in (intent.target_phrase or "").lower()

    assert is_railway_readonly_direct_request("show railway deployment status")


def test_beta_smoke_cross_provider_failover(monkeypatch):
    from aethos_core.llm.effective_model import EffectiveModel
    from aethos_core.provider import completion as completion_mod
    from aethos_core.provider.completion import ProviderResult, _complete_with_failover

    monkeypatch.setenv("USE_REAL_LLM", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
    monkeypatch.setenv("MODEL_FAILOVER_ENABLED", "true")
    get_settings.cache_clear()

    effective = EffectiveModel(
        catalog_id="anthropic:claude-opus-4-6",
        provider="anthropic",
        model="claude-opus-4-6",
        label="Claude Opus 4.6",
        source="session",
    )
    providers_called: list[str] = []

    def fake_attempt(user_text, *, provider, model, include_identity, system_overlay):
        providers_called.append(provider)
        if provider == "anthropic":
            return ProviderResult(
                text="Anthropic temporarily unavailable (timeout)",
                provider="anthropic",
                model=model,
                used_llm=False,
            )
        return ProviderResult(
            text="ok from second provider",
            provider=provider,
            model=model,
            used_llm=True,
            input_tokens=1,
            output_tokens=1,
        )

    with patch.object(completion_mod, "_complete_one_attempt", side_effect=fake_attempt):
        result = _complete_with_failover(
            "summarize status",
            effective,
            include_identity=False,
            system_overlay=None,
            session_id="sess-failover-smoke",
        )

    assert result.used_llm is True
    assert result.provider != "anthropic"
    assert providers_called[0] == "anthropic"
    assert len(set(providers_called)) >= 2
