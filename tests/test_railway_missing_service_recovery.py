# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from aethos_core.operational_session.kernel_planner_bridge import (
    compose_tool_recovery_reply,
    _should_preserve_executor_reply,
    _should_skip_readonly_recovery,
)
from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal
from aethos_core.operational_session.railway_readonly_executor import ReadonlyExecutionResult, _fetch_logs
from aethos_core.operational_session.session_subject import SessionSubject


def test_missing_railway_service_reply_names_target(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.operational_session.railway_readonly_executor._resolve_health_rows",
        lambda *a, **k: [],
    )
    goal = ReadonlyGoal(operation="fetch_logs", log_limit=5, user_text="logs for fake-svc")
    subject = SessionSubject(provider="railway", service="fake-svc", services=["fake-svc"])
    result = _fetch_logs(goal, subject, session_id="t")
    assert result.ok is False
    assert "fake-svc" in result.reply
    assert "show railway projects" in result.reply.lower()


def test_skip_recovery_for_missing_service_fetch_logs():
    result = ReadonlyExecutionResult(
        ok=False,
        reply="No Railway service named **fake-svc** appears in your inventory.\n\nRun `show railway projects`...",
        operation="fetch_logs",
        tool_id="railway.fetch_logs",
    )
    assert _should_skip_readonly_recovery(result, error_code="RAILWAY_TARGET_SERVICE_MISSING") is True
    assert _should_preserve_executor_reply(result) is True


def test_inline_readonly_recovery_counts_as_recovery_applied():
    result = ReadonlyExecutionResult(
        ok=False,
        reply="No Railway service named **fake-svc** appears in your inventory.\n\nRun `show railway projects`...",
        operation="fetch_logs",
        tool_id="railway.fetch_logs",
    )
    assert _should_skip_readonly_recovery(result, error_code="RAILWAY_TARGET_SERVICE_MISSING")
    assert _should_preserve_executor_reply(result)


def test_readonly_recovery_reply_avoids_greenfield_deploy():
    reply = compose_tool_recovery_reply(
        tool_id="railway.fetch_logs",
        error_code="RAILWAY_TARGET_SERVICE_MISSING",
        provider="railway",
        operation="fetch_logs",
    )
    lower = reply.lower()
    assert "greenfield" not in lower
    assert "preflight" not in lower
    assert "show railway projects" in lower


def test_deploy_recovery_reply_keeps_greenfield_path():
    reply = compose_tool_recovery_reply(
        tool_id="railway.verify_deployment",
        error_code="RAILWAY_TARGET_SERVICE_MISSING",
        provider="railway",
        operation="deploy",
    )
    assert "greenfield" in reply.lower()


def test_vercel_missing_project_reply_triggers_readonly_recovery():
    result = ReadonlyExecutionResult(
        ok=False,
        reply="No Vercel project named **invalid-project-xyz** appears in your inventory.\n\nRun `show vercel projects`...",
        operation="fetch_logs",
        tool_id="vercel.fetch_logs",
    )
    assert _should_skip_readonly_recovery(result, error_code="VERCEL_TARGET_PROJECT_MISSING")
    assert _should_preserve_executor_reply(result)


def test_operational_runtime_propagates_kernel_ok(monkeypatch):
    from aethos_core.chat.service import ChatTurnResult
    from aethos_core.operational_session import operational_runtime

    monkeypatch.setattr(
        operational_runtime,
        "get_settings",
        lambda: type("S", (), {"operational_conversation_kernel_enabled": True})(),
    )

    def fake_route(text, *, session_id, channel):
        return ChatTurnResult(
            reply="recovery",
            intent="operational_kernel_fetch_logs",
            meta={"kernel_ok": "false", "recovery_applied": "true"},
        )

    monkeypatch.setattr(
        "aethos_core.operational_session.kernel_router.route_operational_conversation_kernel_turn",
        fake_route,
    )
    out = operational_runtime.run_operational_turn("x", session_id="t", channel="cli")
    assert out.ok is False
