# SPDX-License-Identifier: Apache-2.0
"""KERNEL_004 — automated operational kernel smoke runner."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Literal
from unittest.mock import patch

SmokeStatus = Literal["PASS", "FAIL", "DEGRADED"]


@dataclass
class SmokeScenario:
    scenario_id: str
    lane: str
    channel: str
    prompts: tuple[str, ...]
    expect_in_last: tuple[str, ...] = ()
    session_id: str = ""


@dataclass
class SmokeResult:
    scenario_id: str
    status: SmokeStatus
    lane: str
    channel: str
    evidence: dict[str, str] = field(default_factory=dict)
    error: str = ""


RAILWAY_HEALTH = [
    {"service": "aethos-api", "project": "pilotos", "environment": "staging", "status": "running", "health": "healthy", "deployment_state": "success", "service_id": "svc-api"},
    {"service": "aethos-ui", "project": "pilotos", "environment": "staging", "status": "running", "health": "healthy", "deployment_state": "success", "service_id": "svc-ui"},
]

RAILWAY_CHECKS = {
    "ok": True,
    "railway_credential_ok": True,
    "railway_api_connection_ok": True,
    "inventory": {"ok": True, "project_count": 1, "service_count": 2, "environment_count": 1, "projects": [{"name": "pilotos", "services": ["aethos-api", "aethos-ui"]}]},
}

KILLIT = {"target_id": "dt-killit", "alias": "killit", "vercel_project": "killit", "default_provider": "vercel"}

VERCEL_PROJECTS = {"ok": True, "project_count": 1, "projects": [{"name": "killit", "latest_production_state": "READY"}]}
VERCEL_LOGS = {"ok": True, "project_name": "killit", "events": [{"created": "t", "type": "stdout", "text": "GET / 200"}], "log_lines": [], "deployment": {"state": "READY"}}
VERCEL_DEPLOYMENTS = {"ok": True, "deployments": [{"created_at": "t", "state": "READY", "branch": "main", "url": "https://killit.vercel.app"}]}


SCENARIOS: tuple[SmokeScenario, ...] = (
    SmokeScenario("rail-inv", "railway", "kernel", ("show Railway projects",), ("projects",)),
    SmokeScenario("rail-logs", "railway", "kernel", ("show Railway projects", "show logs"), ("logs",)),
    SmokeScenario("rail-deploy", "railway", "kernel", ("show deployment status on railway",), ("deployment",)),
    SmokeScenario("rail-health", "railway", "kernel", ("check health for aethos-api on railway",), ("health",)),
    SmokeScenario("rail-follow", "railway", "kernel", ("show Railway projects", "what about api?"), ("aethos-api",)),
    SmokeScenario("ver-inv", "vercel", "kernel", ("show vercel projects",), ("vercel",)),
    SmokeScenario("ver-logs", "vercel", "kernel", ("give me top 5 logs for killit",), ("killit",)),
    SmokeScenario("ver-deploy", "vercel", "kernel", ("list vercel deployments for killit",), ("deployments",)),
    SmokeScenario("ver-health", "vercel", "kernel", ("check health for killit on vercel",), ("killit",)),
    SmokeScenario("ver-follow", "vercel", "kernel", ("give me top 5 logs for killit", "can you give me that?"), ("killit",)),
    SmokeScenario("cli-inv", "railway", "cli", ("show railway projects",), ("projects",)),
    SmokeScenario("cli-logs", "railway", "cli", ("show logs",), ("logs",), session_id="smoke-cli-logs"),
    SmokeScenario("cli-continue", "railway", "cli", ("Deploy AethOS to Railway", "continue"), ("Plan step",)),
)


def _railway_patches():
    return [
        patch("aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks", return_value=RAILWAY_CHECKS),
        patch("aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows", return_value=(RAILWAY_HEALTH, None)),
        patch("aethos_core.providers.railway.operations.logs_multisource.fetch_railway_service_logs_fast", return_value={"ok": True, "logs": [{"timestamp": "t", "level": "INFO", "message": "ok", "source": "deployment_logs"}], "sources_checked": ["deployment_logs"]}),
    ]


def _vercel_patches():
    return [
        patch("aethos_core.deployment_targets.registry.match_aliases_in_text", return_value=KILLIT),
        patch("aethos_core.runtime.vercel_readonly_jobs.resolve_vercel_auth_for_chat", return_value={"auth_method": "api_token", "credential_id": "cred-1"}),
        patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token", return_value="token"),
        patch("aethos_core.providers.vercel.diagnostics.project_diagnostics_api.fetch_projects_list", return_value=VERCEL_PROJECTS),
        patch("aethos_core.providers.vercel.operations.logs_api.fetch_deployment_logs", return_value=VERCEL_LOGS),
        patch("aethos_core.providers.vercel.operations.deployments_api.fetch_deployments", return_value=VERCEL_DEPLOYMENTS),
    ]


def run_smoke_scenario(scenario: SmokeScenario) -> SmokeResult:
    from aethos_core.config import get_settings

    settings = get_settings()
    settings.operational_conversation_kernel_enabled = True
    settings.kernel_router_retirement_enabled = True
    settings.vercel_reference_lane_enabled = True
    settings.execution_brain_use_llm = False
    settings.use_real_llm = False

    sid = scenario.session_id or f"smoke-{scenario.scenario_id}"
    patches = []
    if scenario.lane == "railway" or scenario.scenario_id.startswith("cli"):
        patches.extend(_railway_patches())
    if scenario.lane == "vercel" or "killit" in " ".join(scenario.prompts).lower():
        patches.extend(_vercel_patches())
    if scenario.scenario_id == "cli-continue":
        patches.append(
            patch(
                "aethos_core.local_workspace.portfolio.discover_projects",
                return_value={"projects": [{"name": "aethos"}]},
            )
        )

    started = [p.start() for p in patches]
    try:
        last_reply = ""
        last_intent = ""
        for prompt in scenario.prompts:
            if scenario.channel == "cli":
                from aethos_core.operational_session.operational_runtime import run_operational_turn

                turn = run_operational_turn(prompt, session_id=sid, channel="cli")
                if not turn.ok:
                    return SmokeResult(scenario.scenario_id, "FAIL", scenario.lane, scenario.channel, error=turn.reply[:200])
                last_reply = turn.reply
                last_intent = turn.intent
            else:
                from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn

                turn = route_operational_conversation_kernel_turn(prompt, session_id=sid)
                if turn is None:
                    return SmokeResult(scenario.scenario_id, "FAIL", scenario.lane, scenario.channel, error=f"No kernel match: {prompt}")
                last_reply = turn.reply
                last_intent = turn.intent

        lower = last_reply.lower()
        missing = [token for token in scenario.expect_in_last if token.lower() not in lower]
        if missing:
            return SmokeResult(
                scenario.scenario_id,
                "DEGRADED" if last_reply else "FAIL",
                scenario.lane,
                scenario.channel,
                evidence={"reply_preview": last_reply[:240], "intent": last_intent},
                error=f"Missing tokens: {', '.join(missing)}",
            )
        return SmokeResult(
            scenario.scenario_id,
            "PASS",
            scenario.lane,
            scenario.channel,
            evidence={"intent": last_intent, "reply_preview": last_reply[:240]},
        )
    finally:
        for patcher in patches:
            patcher.stop()


def run_kernel_smoke(*, json_out: bool = False) -> dict:
    from aethos_core.operational_session import clear_operational_sessions_for_tests
    from aethos_core.execution_brain.conversation_plan_registry import clear_conversation_plans_for_tests

    clear_operational_sessions_for_tests()
    clear_conversation_plans_for_tests()
    results = [run_smoke_scenario(scenario) for scenario in SCENARIOS]
    passed = sum(1 for row in results if row.status == "PASS")
    total = len(results)
    bundle = {
        "status": "PASS" if passed == total else ("DEGRADED" if passed >= int(total * 0.95) else "FAIL"),
        "passed": passed,
        "total": total,
        "pass_rate": round(100.0 * passed / total, 1) if total else 0.0,
        "ran_at": time.time(),
        "results": [asdict(row) for row in results],
    }
    if json_out:
        print(json.dumps(bundle, indent=2))
    else:
        for row in results:
            print(f"[{row.status}] {row.scenario_id} ({row.lane}/{row.channel})")
        print(f"\nOverall: {bundle['status']} — {passed}/{total} ({bundle['pass_rate']}%)")
    return bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Operational kernel smoke runner")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    bundle = run_kernel_smoke(json_out=args.json)
    return 0 if bundle["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
