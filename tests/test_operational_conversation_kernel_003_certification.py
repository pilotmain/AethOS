# SPDX-License-Identifier: Apache-2.0
"""KERNEL_003 certification — Vercel reference lane, router retirement, unified runtime."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from aethos_core.execution_brain.conversation_plan_registry import clear_conversation_plans_for_tests
from aethos_core.execution_brain.goal_llm_refiner import maybe_refine_operational_goal, maybe_refine_operational_reply
from aethos_core.execution_brain.goal_planner import plan_operational_goal
from aethos_core.operational_session import clear_operational_sessions_for_tests
from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn
from aethos_core.operational_session.operational_runtime import run_operational_turn
from aethos_core.operational_session.router_retirement import (
    WAVE_1_ROUTERS,
    legacy_readonly_router_retired,
    wave_1_retirement_stats,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_operational_sessions_for_tests()
    clear_conversation_plans_for_tests()
    yield
    clear_operational_sessions_for_tests()
    clear_conversation_plans_for_tests()


@pytest.fixture(autouse=True)
def _disable_llm_refinement():
    """Certification must be deterministic — never call live LLM from .env."""
    with patch(
        "aethos_core.execution_brain.goal_llm_refiner.maybe_refine_operational_goal",
        side_effect=lambda plan, **_: plan,
    ), patch(
        "aethos_core.execution_brain.goal_llm_refiner.maybe_refine_operational_reply",
        side_effect=lambda reply, **_: (reply, False),
    ):
        yield


@pytest.fixture
def enable_kernel(monkeypatch):
    from aethos_core.config import get_settings

    s = get_settings()
    monkeypatch.setattr(s, "operational_conversation_kernel_enabled", True)
    monkeypatch.setattr(s, "kernel_router_retirement_enabled", True)
    monkeypatch.setattr(s, "vercel_reference_lane_enabled", True)


KILLIT_ROW = {
    "target_id": "dt-killit",
    "alias": "killit",
    "vercel_project": "killit",
    "default_provider": "vercel",
}

VERCEL_PROJECTS = {
    "ok": True,
    "project_count": 2,
    "projects": [
        {"name": "killit", "latest_production_state": "READY"},
        {"name": "aethos-ui", "latest_production_state": "READY"},
    ],
}

VERCEL_LOGS = {
    "ok": True,
    "project_name": "killit",
    "events": [{"created": "2026-06-01T10:00:00Z", "type": "stdout", "text": "GET / 200"}],
    "log_lines": [],
    "deployment_id": "dpl-killit",
    "deployment": {"state": "READY"},
}

VERCEL_DEPLOYMENTS = {
    "ok": True,
    "deployments": [
        {
            "created_at": "2026-06-01T09:00:00Z",
            "state": "READY",
            "branch": "main",
            "url": "https://killit.vercel.app",
        }
    ],
}


def _vercel_patches():
    return [
        patch("aethos_core.deployment_targets.registry.match_aliases_in_text", return_value=KILLIT_ROW),
        patch(
            "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
            return_value={"auth_method": "api_token", "credential_id": "cred-1"},
        ),
        patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token", return_value="token"),
        patch(
            "aethos_core.providers.vercel.diagnostics.project_diagnostics_api.fetch_projects_list",
            return_value=VERCEL_PROJECTS,
        ),
        patch(
            "aethos_core.providers.vercel.operations.logs_api.fetch_deployment_logs",
            return_value=VERCEL_LOGS,
        ),
        patch(
            "aethos_core.providers.vercel.operations.deployments_api.fetch_deployments",
            return_value=VERCEL_DEPLOYMENTS,
        ),
    ]


@dataclass(frozen=True)
class VercelScript:
    script_id: str
    category: str
    prompts: tuple[str, ...]
    expect_in_last: tuple[str, ...]
    expect_not_in_last: tuple[str, ...] = ()
    needs_killit: bool = True


VERCEL_SCRIPTS: tuple[VercelScript, ...] = (
    VercelScript("v-inv-01", "inventory", ("show vercel projects",), ("vercel", "killit")),
    VercelScript("v-inv-02", "inventory", ("list vercel apps",), ("vercel",)),
    VercelScript("v-inv-03", "inventory", ("vercel project inventory",), ("projects",)),
    VercelScript("v-inv-04", "inventory", ("what are my vercel projects",), ("killit",)),
    VercelScript("v-logs-01", "logs", ("give me top 5 logs for killit",), ("killit", "GET /")),
    VercelScript("v-logs-02", "logs", ("show vercel logs for killit",), ("logs",)),
    VercelScript("v-logs-03", "logs", ("fetch latest logs on vercel for killit",), ("killit",)),
    VercelScript("v-health-01", "health", ("check health for killit on vercel",), ("health", "killit")),
    VercelScript("v-health-02", "health", ("is killit healthy on vercel",), ("ready",)),
    VercelScript("v-deploy-01", "deployments", ("deployment status for killit on vercel",), ("deployment",)),
    VercelScript("v-deploy-02", "deployments", ("show deployment status killit",), ("killit",)),
    VercelScript("v-deploy-03", "deployments", ("list vercel deployments for killit",), ("deployments",)),
    VercelScript("v-deploy-04", "deployments", ("vercel deployments killit",), ("main",)),
    VercelScript("v-deploy-05", "deployments", ("latest deployment killit vercel",), ("ready",)),
    VercelScript("v-follow-01", "followups", ("show vercel projects", "show logs"), ("logs",)),
    VercelScript(
        "v-follow-02",
        "followups",
        ("give me top 5 logs for killit", "can you give me that?"),
        ("killit",),
    ),
    VercelScript("v-follow-03", "followups", ("show vercel projects", "what about killit?"), ("killit",)),
    VercelScript(
        "v-follow-04",
        "followups",
        ("show deployment status killit", "top 5 logs"),
        ("logs",),
    ),
    VercelScript("v-recovery-01", "recovery", ("show vercel logs for killit",), ("killit",)),
    VercelScript("v-recovery-02", "recovery", ("fetch vercel logs killit",), ("No mutation",)),
    VercelScript("v-amb-01", "ambiguity", ("give me top 5 logs for killit", "top 5 only"), ("killit",)),
    VercelScript(
        "v-amb-02",
        "ambiguity",
        ("vercel logs",),
        ("vercel project",),
        needs_killit=False,
    ),
    VercelScript("v-target-01", "targets", ("logs for killit",), ("killit",)),
    VercelScript("v-target-02", "targets", ("vercel killit logs",), ("GET /",)),
    VercelScript("v-inv-05", "inventory", ("show vercel project list",), ("readonly",)),
)


def _run_vercel_script(script: VercelScript, *, session_id: str):
    sid = session_id or f"vercel-{script.script_id}"
    patches = _vercel_patches()
    if not script.needs_killit:
        patches = [
            patch(
                "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
                return_value={"auth_method": "api_token", "credential_id": "cred-1"},
            ),
            patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token", return_value="token"),
        ]
    started = [p.start() for p in patches]
    try:
        last = None
        for prompt in script.prompts:
            last = route_operational_conversation_kernel_turn(prompt, session_id=sid)
            assert last is not None, f"{script.script_id} failed on: {prompt}"
        return last
    finally:
        for patcher in patches:
            patcher.stop()


@pytest.mark.parametrize("script", VERCEL_SCRIPTS, ids=lambda s: s.script_id)
def test_vercel_kernel_script_passes(enable_kernel, script: VercelScript):
    result = _run_vercel_script(script, session_id=f"vercel-cert-{script.script_id}")
    lower = result.reply.lower()
    for token in script.expect_in_last:
        assert token.lower() in lower, f"{script.script_id} missing `{token}`"
    for token in script.expect_not_in_last:
        assert token.lower() not in lower


def test_wave_1_meets_thirty_percent_delegation():
    stats = wave_1_retirement_stats()
    assert stats["deletion_percent"] >= 30.0
    assert stats["wave_2_deleted"] >= 3


@pytest.mark.parametrize(
    "router_id,import_path",
    [
        ("railway_named_service_logs", "aethos_core.chat.railway_named_service_log_router"),
        ("multi_provider_health", "aethos_core.chat.multi_provider_health_router"),
        ("explicit_provider_readonly_diagnostics", "aethos_core.operational_target_resolution.routing"),
    ],
)
def test_wave_2_deleted_router_modules_removed(router_id, import_path):
    import importlib

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(import_path)


def test_railway_projects_inventory_route_removed():
    from aethos_core.providers.railway.inventory import railway_projects_chat

    assert not hasattr(railway_projects_chat, "route_railway_projects_inventory")


def test_vercel_readonly_compose_returns_none(enable_kernel):
    from aethos_core.provider_readonly_intent.readonly_provider_router import compose_readonly_provider_route_reply

    assert compose_readonly_provider_route_reply("show vercel logs for killit", session_id="x") is None


def test_unified_runtime_matches_kernel(enable_kernel):
    with patch(
        "aethos_core.deployment_targets.registry.match_aliases_in_text",
        return_value=KILLIT_ROW,
    ), patch(
        "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
        return_value={"auth_method": "api_token", "credential_id": "cred-1"},
    ), patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token",
        return_value="token",
    ), patch(
        "aethos_core.providers.vercel.operations.logs_api.fetch_deployment_logs",
        return_value=VERCEL_LOGS,
    ):
        cli = run_operational_turn("give me top 5 logs for killit", session_id="cli-unified", channel="cli")
        chat = route_operational_conversation_kernel_turn("give me top 5 logs for killit", session_id="chat-unified")
    assert cli.ok and chat is not None
    assert "killit" in cli.reply.lower()
    assert "killit" in chat.reply.lower()
    assert cli.meta.get("channel") == "cli"


def test_llm_refiner_default_off(enable_kernel, monkeypatch):
    from aethos_core.config import get_settings
    from aethos_core.operational_session.active_subject_resolver import resolve_active_subject
    from aethos_core.operational_session.operational_session import load_operational_session

    monkeypatch.setattr(get_settings(), "execution_brain_use_llm", False)
    session = load_operational_session(session_id="llm-off")
    subject = resolve_active_subject("show vercel projects", session_id="llm-off").subject
    plan = plan_operational_goal("show vercel projects", subject=subject, session=session)
    assert plan is not None
    refined = maybe_refine_operational_goal(plan, user_text="show vercel projects", session_id="llm-off")
    assert refined.headline == plan.headline
    reply, used = maybe_refine_operational_reply("Hello **killit**", goal_kind="readonly_execute", provider="vercel")
    assert reply == "Hello **killit**"
    assert used is False


def test_wave_1_catalog_has_required_dispositions():
    dispositions = {row["disposition"] for row in WAVE_1_ROUTERS.values()}
    assert "DELETED_WAVE_2" in dispositions
    assert "KEEP_TEMPORARILY" in dispositions
    assert "REQUIRES_KERNEL_FEATURE" in dispositions
