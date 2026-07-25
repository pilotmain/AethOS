# SPDX-License-Identifier: Apache-2.0
"""P0–P2 operator platform parity tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_runtime_state(tmp_path, monkeypatch):
    monkeypatch.setenv("OPERATOR_RUNTIME_STATE_PATH", str(tmp_path / "operator_runtime.json"))
    from aethos_core.autonomous_execution.runtime_state import reset_runtime_state_cache_for_tests
    from aethos_core.operational_skill_runtime.skill_loader import reset_local_operator_skills_cache_for_tests

    reset_runtime_state_cache_for_tests()
    reset_local_operator_skills_cache_for_tests()
    yield


def test_autonomous_execution_plane_noop_and_planned(monkeypatch) -> None:
    monkeypatch.setenv("AUTONOMOUS_EXECUTION_PLANE_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.autonomous_execution.plane_service import (
        dispatch_until_idle,
        submit_noop_task,
        submit_planned_task,
    )

    noop = submit_noop_task()
    assert noop["ok"] is True
    planned = submit_planned_task(steps=[{"step_id": "s1", "type": "noop"}, {"step_id": "s2", "type": "noop"}])
    assert planned["ok"] is True
    result = dispatch_until_idle()
    assert result["ticks"] >= 1
    terminals = {row.get("terminal") for row in result.get("results") or []}
    assert "completed" in terminals


def test_task_registry_persist_restore(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPERATOR_RUNTIME_STATE_PATH", str(tmp_path / "state.json"))
    from aethos_core.autonomous_execution.runtime_state import load_runtime_state, save_runtime_state
    from aethos_core.autonomous_execution import task_registry

    st = load_runtime_state()
    tid = task_registry.put_task(st, {"type": "noop", "state": "queued"})
    save_runtime_state(st)
    st2 = load_runtime_state(force=True)
    assert task_registry.get_task(st2, tid)["state"] == "queued"


def test_execution_checkpoint_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPERATOR_RUNTIME_STATE_PATH", str(tmp_path / "state.json"))
    from aethos_core.autonomous_execution.execution_checkpoint import get_checkpoint, save_checkpoint
    from aethos_core.autonomous_execution.execution_plan import create_plan
    from aethos_core.autonomous_execution.runtime_state import load_runtime_state, save_runtime_state

    st = load_runtime_state()
    pid = create_plan(st, "t1", [{"step_id": "s1"}])
    save_checkpoint(st, pid, "s1", task_id="t1", outputs=[{"x": 1}])
    save_runtime_state(st)
    st2 = load_runtime_state(force=True)
    cp = get_checkpoint(st2, pid, "s1")
    assert cp and cp.get("outputs") == [{"x": 1}]


def test_slack_adapter_normalizes_event() -> None:
    from aethos_core.channels.slack.slack_adapter import SlackChannelAdapter

    adapter = SlackChannelAdapter()
    msg = adapter.normalize_payload(
        {
            "type": "event_callback",
            "event": {"type": "message", "text": "status update", "channel": "C1", "user": "U1"},
        }
    )
    assert msg is not None
    assert msg.text == "status update"
    assert msg.external_chat_id == "C1"


def test_slack_url_verification_challenge() -> None:
    from aethos_core.channels.slack.slack_router import handle_slack_event

    out = handle_slack_event({"type": "url_verification", "challenge": "abc123"})
    assert out.get("challenge") == "abc123"


def test_aws_skill_discover_without_boto3(monkeypatch) -> None:
    from aethos_core.provider_skills.aws.skill import AwsProviderSkill, _readonly_inventory

    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIA_TEST")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    skill = AwsProviderSkill()
    monkeypatch.setattr(
        "aethos_core.provider_skills.aws.skill._readonly_inventory",
        lambda *, region: {"ok": False, "error": "boto3 not installed — add optional dependency `aethos[cloud]`.", "provider": "aws", "region": region},
    )
    payload = skill.discover(force=True)
    assert payload["ok"] is False
    assert "boto3" in str(payload.get("error") or "")


def test_vercel_greenfield_intent() -> None:
    from aethos_core.providers.vercel.greenfield_deployment.greenfield_intent import (
        is_vercel_greenfield_deployment_intent,
    )

    assert is_vercel_greenfield_deployment_intent("create a new vercel project and deploy from local")
    assert not is_vercel_greenfield_deployment_intent("show vercel projects")


def test_github_workflow_dispatch_api(monkeypatch) -> None:
    from aethos_core.providers.github.operations.workflow_dispatch_api import dispatch_workflow

    def fake_request(token, method, path, *, params=None, json_body=None):
        assert method == "POST"
        assert "dispatches" in path
        return {"ok": True, "http_status": 204}

    monkeypatch.setattr(
        "aethos_core.providers.github.operations.workflow_dispatch_api.request_github",
        fake_request,
    )
    out = dispatch_workflow("tok", repository="owner/repo", workflow_id="deploy.yml", ref="main")
    assert out["ok"] is True


def test_local_skills_loader_finds_repo_skill() -> None:
    from aethos_core.operational_skill_runtime.skill_loader import load_local_operator_skills

    payload = load_local_operator_skills(force=True)
    assert payload["ok"] is True
    assert payload["count"] >= 1
    assert any(row.get("id") == "deployment-status" for row in payload.get("skills") or [])


def test_mcp_bridge_disabled_by_default(monkeypatch) -> None:
    monkeypatch.setenv("MCP_BRIDGE_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.operational_skill_runtime.skill_loader import invoke_mcp_tool

    out = invoke_mcp_tool("aethos_health")
    assert out["ok"] is False


def test_mcp_bridge_health_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("MCP_BRIDGE_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.operational_skill_runtime.skill_loader import invoke_mcp_tool

    out = invoke_mcp_tool("aethos_health")
    assert out["ok"] is True
    assert "result" in out


def test_vector_memory_recall(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("VECTOR_MEMORY_ENABLED", "true")
    monkeypatch.setenv("OPERATIONAL_ENVIRONMENT", "development")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.memory import vector_store

    monkeypatch.setattr(vector_store, "_memory_path", lambda: tmp_path / "vector_memory.json")
    remember = vector_store.remember
    recall = vector_store.recall

    remember(text="railway deployment succeeded for aethos-api", tags=["deploy"])
    out = recall(query="railway deployment", limit=3)
    assert out["ok"] is True
    assert len(out.get("matches") or []) >= 1
    match = out["matches"][0]
    assert match.get("embedding") is None
    assert match.get("environment") == "development"


def test_operational_environment_banner(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("OPERATIONAL_ENVIRONMENT", "staging")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.runtime.operational_environment import resolve_operational_environment, stamp_external_channel_reply

    snap = resolve_operational_environment()
    assert snap.canonical == "staging"
    # The environment banner is still resolvable on demand (CLI / runtime status)…
    assert "Staging" in snap.banner
    # …but it is no longer prepended to conversational replies on any channel
    # (it was noisy on casual chit-chat over Telegram/SMS).
    stamped = stamp_external_channel_reply("hello", channel="sms")
    assert stamped == "hello"
    assert "**Environment:**" not in stamped


def test_email_adapter_send_uses_smtp(monkeypatch) -> None:
    monkeypatch.setenv("EMAIL_ENABLED", "true")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("EMAIL_FROM", "ops@example.com")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.channels.universal.universal_channel_runtime import EmailAdapter

    adapter = EmailAdapter()
    assert adapter.is_configured()
    sent: list[str] = []

    def fake_send(**kwargs):
        sent.append(kwargs["to_addr"])
        return True

    monkeypatch.setattr("aethos_core.channels.universal.universal_channel_runtime._send_smtp_email", fake_send)
    assert adapter.send_message(chat_id="user@example.com", text="ok") is True
    assert sent == ["user@example.com"]


def test_gcp_skill_without_gcloud(monkeypatch) -> None:
    from aethos_core.provider_skills.gcp.skill import GcpProviderSkill

    monkeypatch.setattr("aethos_core.provider_skills.gcp.skill.shutil.which", lambda _: None)
    skill = GcpProviderSkill()
    payload = skill.discover(force=True)
    assert payload["ok"] is False


def test_azure_skill_without_az(monkeypatch) -> None:
    from aethos_core.provider_skills.azure.skill import AzureProviderSkill

    monkeypatch.setattr("aethos_core.provider_skills.azure.skill.shutil.which", lambda _: None)
    skill = AzureProviderSkill()
    payload = skill.discover(force=True)
    assert payload["ok"] is False


def test_vercel_create_project_api(monkeypatch) -> None:
    from aethos_core.providers.vercel import api_client

    def fake_request(token, path, *, params=None, timeout_sec=None, method="GET", json_body=None):
        assert method == "POST"
        assert path == "/v10/projects"
        assert json_body and json_body.get("name") == "demo-app"
        return {"id": "prj_1", "name": "demo-app"}

    monkeypatch.setattr(api_client, "_request", fake_request)
    out = api_client.create_project("tok", name="demo-app", git_repo="org/repo", framework="nextjs")
    assert out["id"] == "prj_1"


def test_channel_inbound_stamps_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("OPERATIONAL_ENVIRONMENT", "development")
    monkeypatch.setenv("CHANNEL_GATEWAY_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.channels.base.channel_adapter import ChannelMessage
    from aethos_core.channels import inbound
    from aethos_core.chat import service as chat_service

    class _Result:
        reply = "pong"
        intent = "test"
        used_llm = False
        meta: dict = {}

    monkeypatch.setattr(chat_service, "resolve_chat_turn", lambda text, session_id, channel: _Result())
    monkeypatch.setattr(
        "aethos_core.chat.cognition_exception_boundary.sanitize_chat_result_for_transport",
        lambda r: r,
    )
    turn = inbound.handle_channel_message(
        ChannelMessage(
            channel="sms",
            external_user_id="+1555",
            external_chat_id="+1555",
            text="ping",
            session_id="sms:+1555",
            raw={},
        )
    )
    assert "Development" in turn.reply
    assert "pong" in turn.reply


def test_autonomous_execution_tool_shell_when_host_enabled(monkeypatch) -> None:
    monkeypatch.setenv("HOST_EXECUTOR_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.autonomous_execution.tool_step import execute_tool_step

    result = execute_tool_step({"type": "shell", "tool": {"name": "shell", "input": {"command": "echo ok"}}})
    assert result.get("ok") is True


def test_followups_proof_category_for_continuity_prompts() -> None:
    from aethos_core.operational_session.kernel_reality_registry import classify_proof_category

    assert classify_proof_category(operation="", intent="", request="what about api?") == "followups"
    assert classify_proof_category(operation="", intent="", request="top 5 only") == "followups"
    assert classify_proof_category(operation="", intent="deploy_plan", request="continue") == "continue"


def test_operational_session_meta_last_provider() -> None:
    from aethos_core.operational_session import clear_operational_sessions_for_tests
    from aethos_core.operational_session.operational_session import operational_session_meta, record_operational_turn
    from aethos_core.operational_session.session_subject import SessionSubject

    clear_operational_sessions_for_tests()
    subject = SessionSubject(provider="railway", project="aethos", service="aethos-api", environment="production")
    record_operational_turn(
        session_id="meta-test",
        user_text="show logs",
        subject=subject,
        operation="fetch_logs",
        reply_intent="operational_logs",
        result_summary="ok",
    )
    meta = operational_session_meta(session_id="meta-test")
    assert meta["last_provider"] == "railway"
    assert "aethos-api" in str(meta["last_subject_label"])
    assert meta["has_active_subject"] is True


def test_operator_session_registry_persist(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPERATOR_RUNTIME_STATE_PATH", str(tmp_path / "operator_runtime.json"))
    from aethos_core.autonomous_execution.runtime_state import (
        operator_session_registry,
        register_operator_session,
        reset_runtime_state_cache_for_tests,
    )

    reset_runtime_state_cache_for_tests()
    register_operator_session(session_id="cli:demo", channel="cli", last_provider="vercel", last_operation="list_inventory")
    snap = operator_session_registry(session_id="cli:demo")
    assert snap["ok"] is True
    assert snap["session"]["last_provider"] == "vercel"


def test_mission_control_live_updates_recent() -> None:
    from aethos_core.mission_control.live_updates.live_update_bus import (
        publish_live_update,
        recent_live_updates,
        reset_live_update_bus_for_tests,
    )

    reset_live_update_bus_for_tests()
    publish_live_update(event_type="deploy_status", payload={"provider": "railway"})
    rows = recent_live_updates(limit=5)
    assert len(rows) == 1
    assert rows[0]["type"] == "deploy_status"


def test_cloud_readonly_inventory_routes_to_k8s_skill(monkeypatch) -> None:
    monkeypatch.setenv("CLOUD_READONLY_INVENTORY_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.providers.cloud.readonly_inventory import fetch_cloud_readonly_inventory

    monkeypatch.setattr(
        "aethos_core.provider_skills.kubernetes.skill._kubectl_inventory",
        lambda: {"ok": False, "error": "kubectl not found.", "provider": "kubernetes"},
    )
    out = fetch_cloud_readonly_inventory(provider="kubernetes")
    assert out["provider"] == "kubernetes"
    assert "kubectl" in str(out.get("error") or out.get("inventory", {}).get("error") or "")
