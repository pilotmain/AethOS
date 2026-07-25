# SPDX-License-Identifier: Apache-2.0
"""Proactive automation — schedules, webhooks, governance (PATH §2)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.automation.cron_match import cron_matches
from aethos_core.automation.executor import execute_scheduled_task, execute_webhook_trigger
from aethos_core.automation.scheduler import run_due_scheduled_tasks
from aethos_core.automation.store import (
    clear_automation_for_tests,
    create_scheduled_task,
    create_webhook_trigger,
    list_scheduled_tasks,
)
from aethos_core.config import get_settings
from aethos_core.jobs.job_notifications import clear_job_notifications_for_tests
from aethos_core.tenancy.tenant_context import tenant_scope


@pytest.fixture(autouse=True)
def _reset_automation_state(monkeypatch):
    clear_automation_for_tests()
    clear_job_notifications_for_tests()
    monkeypatch.setenv("PROACTIVE_AUTOMATION_ENABLED", "true")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    yield
    clear_automation_for_tests()
    clear_job_notifications_for_tests()
    monkeypatch.delenv("PROACTIVE_AUTOMATION_ENABLED", raising=False)
    monkeypatch.delenv("MULTI_TENANT_ENABLED", raising=False)


def test_cron_matches_daily_slot():
    from datetime import datetime, timezone

    dt = datetime(2026, 6, 8, 9, 0, tzinfo=timezone.utc)
    assert cron_matches("0 9 * * *", dt)
    assert not cron_matches("0 10 * * *", dt)


def test_scheduled_task_runs_chat_and_delivers(monkeypatch):
    with tenant_scope("tenant-a"):
        task = create_scheduled_task(
            name="Ping",
            prompt="Say hello",
            schedule_kind="interval",
            interval_sec=60,
            delivery_channel="web",
            delivery_target="default",
        )

    fake_turn = type("Turn", (), {"reply": "Hello from automation", "meta": {}})()

    with patch("aethos_core.chat.service.resolve_chat_turn", return_value=fake_turn):
        result = execute_scheduled_task(task["task_id"], tenant_id="tenant-a", force=True)

    assert result["ok"] is True
    assert result["result"]["mode"] == "chat"
    assert result["delivery"]["ok"] is True


def test_webhook_trigger_runs_governed_job(monkeypatch):
    with tenant_scope("tenant-b"):
        trigger = create_webhook_trigger(
            name="Deploy hook",
            prompt="Check deploy health",
            action_kind="governed_job",
            job_type="research_scan",
            allow_mutation=False,
        )

    fake_job = {"job_id": "job-1", "status": "queued"}
    with patch(
        "aethos_core.jobs.job_runtime.create_governed_job",
        return_value={"ok": True, "job": fake_job, "requires_approval": False},
    ):
        result = execute_webhook_trigger(
            trigger["trigger_id"],
            secret=trigger["secret"],
            payload={"event": "deploy"},
            tenant_id="tenant-b",
            force=True,
        )

    assert result["ok"] is True
    assert result["result"]["mode"] == "governed_job"
    assert result["delivery"]["ok"] is True


def test_mutation_webhook_requires_approval_without_allow_mutation(monkeypatch):
    with tenant_scope("tenant-c"):
        trigger = create_webhook_trigger(
            name="Mutation hook",
            prompt="Restart provider",
            action_kind="governed_job",
            job_type="provider_restart",
            allow_mutation=False,
        )

    with patch(
        "aethos_core.jobs.job_runtime.create_governed_job",
        return_value={
            "ok": True,
            "job": {"job_id": "job-2", "status": "awaiting_approval"},
            "requires_approval": True,
        },
    ) as create_job:
        result = execute_webhook_trigger(
            trigger["trigger_id"],
            secret=trigger["secret"],
            payload={},
            tenant_id="tenant-c",
            force=True,
        )

    assert result["ok"] is True
    assert result["result"]["requires_approval"] is True
    create_job.assert_called_once()
    assert create_job.call_args.kwargs.get("auto_dispatch") is False


def test_scheduler_ticks_due_interval_task(monkeypatch):
    with tenant_scope("tenant-d"):
        task = create_scheduled_task(
            name="Interval",
            prompt="tick",
            interval_sec=60,
        )
        # Force last_run far in the past via update
        from aethos_core.automation.store import update_scheduled_task

        update_scheduled_task(task["task_id"], {"last_run_at": 0})

    fake_turn = type("Turn", (), {"reply": "tick ok", "meta": {}})()
    with patch("aethos_core.chat.service.resolve_chat_turn", return_value=fake_turn):
        tick = run_due_scheduled_tasks(force=False)

    assert task["task_id"] in tick["ran"]
    with tenant_scope("tenant-d"):
        rows = list_scheduled_tasks()
    assert rows[0]["last_status"] == "ok"


def test_webhook_rejects_bad_secret():
    with tenant_scope("tenant-e"):
        trigger = create_webhook_trigger(name="Secure", prompt="noop")
    result = execute_webhook_trigger(
        trigger["trigger_id"],
        secret="wrong-secret",
        tenant_id="tenant-e",
        force=True,
    )
    assert result["ok"] is False
    assert result["reason"] == "invalid_secret"
