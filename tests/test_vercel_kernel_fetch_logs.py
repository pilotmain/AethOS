# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal
from aethos_core.operational_session.session_subject import SessionSubject
from aethos_core.operational_session.vercel_readonly_executor import _fetch_logs


def test_fetch_logs_partial_success_when_events_empty(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.operational_session.vercel_readonly_executor._resolve_token",
        lambda: ("tok", "cred"),
    )
    monkeypatch.setattr(
        "aethos_core.providers.vercel.operations.logs_api.fetch_deployment_logs",
        lambda *_a, **_k: {
            "ok": False,
            "deployment_id": "dpl_ready",
            "deployment": {"id": "dpl_ready", "state": "ready"},
            "deployments_tried": 2,
            "events": [],
            "log_lines": [],
            "error": "No log lines returned",
            "api_limited": True,
        },
    )
    goal = ReadonlyGoal(operation="fetch_logs", log_limit=5, user_text="top 5 logs for killit")
    subject = SessionSubject(provider="vercel", vercel_project="killit", project="killit")
    result = _fetch_logs(goal, subject, project_name="killit", session_id="t1")
    assert result.ok is True
    assert "dpl_ready" in result.reply
    assert "ready" in result.reply.lower()
    assert "vercel.fetch_logs" == result.tool_id
