# SPDX-License-Identifier: Apache-2.0
"""KERNEL_002 certification — 25 multi-turn operational scripts."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from aethos_core.execution_brain.conversation_plan_registry import clear_conversation_plans_for_tests, load_conversation_plan
from aethos_core.operational_session import clear_operational_sessions_for_tests
from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn


@pytest.fixture(autouse=True)
def _clean():
    clear_operational_sessions_for_tests()
    clear_conversation_plans_for_tests()
    yield
    clear_operational_sessions_for_tests()
    clear_conversation_plans_for_tests()


@pytest.fixture(autouse=True)
def _disable_llm_refinement():
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
    monkeypatch.setattr(s, "execution_brain_use_llm", False)
    monkeypatch.setattr(s, "use_real_llm", False)


def _health_rows():
    return [
        {
            "service": "aethos-api",
            "project": "pilotos",
            "environment": "staging",
            "status": "running",
            "health": "healthy",
            "deployment_state": "success",
            "service_id": "svc-api",
        },
        {
            "service": "aethos-ui",
            "project": "pilotos",
            "environment": "staging",
            "status": "running",
            "health": "healthy",
            "deployment_state": "success",
            "service_id": "svc-ui",
        },
    ]


def _inventory():
    return {
        "ok": True,
        "project_count": 1,
        "service_count": 2,
        "environment_count": 1,
        "projects": [{"name": "pilotos", "services": ["aethos-api", "aethos-ui"]}],
    }


def _checks():
    return {"railway_credential_ok": True, "railway_api_connection_ok": True, "inventory": _inventory()}


def _fake_logs(*, service_name: str, limit: int = 5, **kwargs):
    return {
        "ok": True,
        "logs": [{"timestamp": "2026-06-01T12:00:00Z", "level": "INFO", "message": f"{service_name} ok", "source": "deployment_logs"}],
        "sources_checked": ["deployment_logs"],
    }


@dataclass(frozen=True)
class KernelScript:
    script_id: str
    category: str
    prompts: tuple[str, ...]
    expect_in_last: tuple[str, ...]
    expect_not_in_last: tuple[str, ...] = ()
    session_id: str = ""


SCRIPTS: tuple[KernelScript, ...] = (
    KernelScript("inv-01", "inventory", ("show Railway projects",), ("projects",)),
    KernelScript("inv-02", "inventory", ("list railway services",), ("services", "railway")),
    KernelScript("logs-01", "logs", ("show Railway logs",), ("logs",)),
    KernelScript("logs-02", "logs", ("top 5 logs for aethos-api on railway",), ("aethos-api",)),
    KernelScript("health-01", "health", ("check health for aethos-api on railway",), ("health",)),
    KernelScript("deploy-01", "deploy_planning", ("Deploy AethOS to Railway",), ("Goal:", "railway.validate_token")),
    KernelScript("deploy-02", "deploy_planning", ("deploy aethos to railway with env vars",), ("governed plan",)),
    KernelScript("recovery-01", "recovery", ("show Railway projects",), ("projects",)),
    KernelScript("follow-01", "followups", ("show Railway projects", "show logs"), ("logs",)),
    KernelScript("follow-02", "followups", ("show Railway projects", "what about api?"), ("aethos-api",)),
    KernelScript("target-01", "targets", ("logs for aethos-ui on railway",), ("aethos-ui",)),
    KernelScript("workspace-01", "workspace", ("Deploy AethOS to Railway", "continue"), ("Workspace discovery",)),
    KernelScript("git-01", "git", ("Deploy AethOS to Railway",), ("git.resolve_remote",)),
    KernelScript("status-01", "deployments", ("show deployment status on railway",), ("deployment",)),
    KernelScript("killit-01", "vercel", ("give me top 5 logs for killit",), ("killit",)),
    KernelScript("inv-03", "inventory", ("railway project inventory",), ("railway",)),
    KernelScript("logs-03", "logs", ("fetch latest logs on railway",), ("logs",)),
    KernelScript("health-02", "health", ("is aethos-api healthy on railway",), ("health",)),
    KernelScript("follow-03", "followups", ("show Railway projects", "top 5 only"), ("logs",)),
    KernelScript("deploy-03", "deploy_planning", ("what steps to deploy aethos to railway",), ("Goal:",)),
    KernelScript("recovery-02", "recovery", ("show Railway logs",), ("logs",)),
    KernelScript("target-02", "targets", ("logs for aethos-api on railway",), ("aethos-api",)),
    KernelScript("plan-01", "deploy_planning", ("Deploy AethOS to Railway", "continue"), ("Plan step",)),
    KernelScript("follow-04", "followups", ("give me top 5 logs for killit", "can you give me that?"), ("killit",)),
    KernelScript("health-03", "health", ("check railway health for aethos-ui",), ("health",)),
)


def _run_script(script: KernelScript, *, session_id: str):
    sid = session_id or f"kernel-{script.script_id}"
    patches = []
    if script.category in {"inventory", "followups", "recovery", "workspace", "git", "deploy_planning"}:
        patches.append(
            patch(
                "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
                return_value=_checks(),
            )
        )
    if script.category in {"logs", "followups", "health", "deployments", "targets", "recovery"} or "logs" in script.script_id:
        patches.append(
            patch(
                "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
                return_value=(_health_rows(), None),
            )
        )
        patches.append(
            patch(
                "aethos_core.providers.railway.operations.logs_multisource.fetch_railway_service_logs_fast",
                side_effect=_fake_logs,
            )
        )
    if script.category == "vercel" or script.script_id.startswith("killit") or "killit" in " ".join(script.prompts).lower():
        killit_row = {
            "target_id": "dt-killit",
            "alias": "killit",
            "vercel_project": "killit",
            "default_provider": "vercel",
        }
        patches.extend(
            [
                patch("aethos_core.deployment_targets.registry.match_aliases_in_text", return_value=killit_row),
                patch(
                    "aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat",
                    return_value={"auth_method": "api_token", "credential_id": "cred-1"},
                ),
                patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token", return_value="token"),
                patch(
                    "aethos_core.providers.vercel.operations.logs_api.fetch_deployment_logs",
                    return_value={
                        "ok": True,
                        "project_name": "killit",
                        "events": [{"created": "2026-06-01T10:00:00Z", "type": "stdout", "text": "GET / 200"}],
                        "log_lines": [],
                    },
                ),
            ]
        )
    if script.script_id == "workspace-01":
        patches.append(
            patch(
                "aethos_core.local_workspace.portfolio.discover_projects",
                return_value={"projects": [{"name": "aethos"}, {"name": "killit"}]},
            )
        )

    last = None
    for patcher in patches:
        patcher.start()
    try:
        for prompt in script.prompts:
            last = route_operational_conversation_kernel_turn(prompt, session_id=sid)
            assert last is not None, f"{script.script_id} failed on prompt: {prompt}"
    finally:
        for patcher in patches:
            patcher.stop()
    return last


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda s: s.script_id)
def test_kernel_script_passes(enable_kernel, script: KernelScript):
    result = _run_script(script, session_id=f"cert-{script.script_id}")
    assert result is not None
    lower = result.reply.lower()
    for token in script.expect_in_last:
        assert token.lower() in lower, f"{script.script_id} missing `{token}` in: {result.reply[:200]}"
    for token in script.expect_not_in_last:
        assert token.lower() not in lower


def test_deploy_plan_persisted_for_continue(enable_kernel):
    with patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        return_value=_checks(),
    ):
        route_operational_conversation_kernel_turn("Deploy AethOS to Railway", session_id="plan-continue")
    plan = load_conversation_plan(session_id="plan-continue")
    assert plan is not None
    assert plan.goal_kind == "deploy_planning"
    assert plan.graph is not None
    assert len(plan.graph.steps) >= 5
