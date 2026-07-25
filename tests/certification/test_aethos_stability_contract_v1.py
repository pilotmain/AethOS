# SPDX-License-Identifier: Apache-2.0
"""FIX 105 — Stability contract v1: freeze certified lanes without live provider calls."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from aethos_core.chat.route_trace import save_last_route_trace
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
    route_workflow_lane,
)
from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
    get_creation_preflight,
)
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    get_deployment_plan_context,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    clear_for_tests as clear_execution_context,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    list_execution_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    resolve_execution_id_for_plan,
)
from tests.certification.helpers import (
    assert_no_generic_capability_prose,
    assert_route_did_not_call_provider,
    assert_route_owns,
    reset_certification_runtime,
)
from tests.certification.test_aethos_core_certification import _resolved_railway_gate

pytestmark = pytest.mark.certification


@pytest.fixture(autouse=True)
def _stability_clean():
    reset_certification_runtime()
    clear_journal()
    clear_receipts()
    clear_execution_context()
    get_settings.cache_clear()
    yield
    clear_journal()
    clear_receipts()
    clear_execution_context()
    get_settings.cache_clear()
    reset_certification_runtime()


def _passed_readiness_checks() -> dict:
    return {
        "readonly_readiness_ok": True,
        "mutation_ready": False,
        "railway_credential_ok": True,
        "referenced_github_repo": "pilotmain/aethos",
        "required_env_vars": ["RAILWAY_API_TOKEN"],
        "inventory": {
            "ok": True,
            "project_count": 1,
            "environment_count": 1,
            "service_count": 1,
            "projects": [],
        },
        "github_binding": {"github_credential_ok": True},
        "service_creation": {"graphql_service_create": False},
        "execution_mode": "api",
    }


def _simulator_checks_pass() -> list[dict]:
    return [
        {"check": "railway_project_environment", "status": "pass", "details": "ok"},
        {"check": "service_name_availability", "status": "pass", "details": "ok"},
        {"check": "github_source_binding", "status": "pass", "details": "ok"},
        {"check": "railway_credential_readiness", "status": "pass", "details": "ok"},
        {
            "check": "required_env_var_readiness",
            "status": "pass",
            "env_var_names_status": "pass",
            "env_var_values_status": "pass",
            "details": "ok",
        },
        {"check": "build_start_health_readiness", "status": "pass", "details": "ok"},
        {"check": "rollback_readiness", "status": "pass", "details": "ok"},
        {"check": "execution_api_surface", "status": "pass", "details": "ok"},
    ]


@contextmanager
def _railway_dry_run_lifecycle_mocks(monkeypatch):
    import os

    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "dry_run")
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOWED_ENVIRONMENTS", "staging,development,production")
    os.environ["RAILWAY_GREENFIELD_EXECUTION_MODE"] = "dry_run"
    get_settings.cache_clear()
    inspect_payload = {
        "ok": True,
        "repository": "pilotmain/aethos",
        "branch": "main",
        "fields": {
            "runtime": "Python",
            "build_command": "pip install -r requirements.txt",
            "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
            "health_check_path": "/api/v1/health",
            "required_env_var_names": ["APP_ENV"],
            "service_name_confidence": "medium",
        },
    }
    with (
        patch(
            "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks",
            return_value=_passed_readiness_checks(),
        ),
        patch(
            "aethos_core.providers.railway.deployment_plan.deployment_plan_artifact.list_railway_project_environment_options",
            return_value=[],
        ),
        patch(
            "aethos_core.providers.railway.deployment_plan.plan_completion.inspect_github_repo_for_deployment",
            return_value=inspect_payload,
        ),
        patch(
            "aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks",
            return_value=_simulator_checks_pass(),
        ),
        patch(
            "aethos_core.providers.railway.env_value_readiness.env_value_inventory.probe_env_var_presence",
            return_value={"present": True, "secret": False, "source": "configured"},
        ),
    ):
        yield


class TestStabilityContractRailwayDryRunLifecycle:
    """Full governed Railway lifecycle — fixtures only, dry_run execution, no live mutation."""

    def test_railway_dry_run_lifecycle_prompt_chain(self, monkeypatch) -> None:
        session = "stability-contract-railway-v1"
        with _railway_dry_run_lifecycle_mocks(monkeypatch):
            readiness = resolve_chat_turn(
                "run railway deployment readiness for pilotmain/aethos",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(readiness, route_id="railway_deployment_readiness")
            assert readiness.meta.get("mutation_performed") in {None, "false"}
            assert_no_generic_capability_prose(readiness)

            plan = resolve_chat_turn(
                "create railway deployment plan for pilotmain/aethos in pilotos / staging",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(plan, route_id="railway_deployment_plan")
            assert plan.intent == "railway_deployment_plan_draft"
            assert "readiness must pass" not in plan.reply.lower()
            stored_plan = get_deployment_plan_context(session_id=session)
            assert stored_plan is not None
            assert str(stored_plan.get("environment") or "").lower() == "staging"

            complete = resolve_chat_turn(
                "complete the railway deployment plan",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(complete, route_id="railway_deployment_plan")
            assert complete.intent == "railway_deployment_plan_complete"
            assert complete.meta.get("mutation_performed") == "false"

            review = resolve_chat_turn(
                "review railway deployment plan",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(review, route_id="railway_deployment_plan")
            assert review.intent == "railway_deployment_plan_review"

            confirm = resolve_chat_turn(
                "confirm railway deployment plan",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(confirm, route_id="railway_deployment_plan")
            assert confirm.intent == "railway_deployment_plan_confirm"
            assert confirm.meta.get("mutation_performed") == "false"

            preflight = resolve_chat_turn(
                "create railway service creation preflight",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(preflight, route_id="railway_deployment_creation_preflight")
            assert preflight.meta.get("mutation_performed") == "false"
            assert get_creation_preflight(session_id=session) is not None

            approve = resolve_chat_turn(
                "approve railway service creation preflight",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(approve, route_id="railway_deployment_creation_preflight")
            assert approve.meta.get("mutation_performed") == "false"
            assert get_creation_preflight(session_id=session) is not None
            assert get_creation_preflight(session_id=session).get("preflight_approved") is True

            simulate = resolve_chat_turn(
                "simulate railway service creation",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(simulate, route_id="railway_service_creation_simulator")
            assert simulate.meta.get("mutation_performed") == "false"
            assert "No mutation has been performed" in simulate.reply
            from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
                get_simulation,
                save_simulation,
            )

            sim_snapshot = get_simulation(session_id=session)
            assert sim_snapshot is not None
            sim_snapshot["ready_to_execute"] = True
            sim_snapshot["blocking_reasons"] = []
            sim_snapshot["blocking_reason_messages"] = []
            save_simulation(session_id=session, simulation=sim_snapshot)
            get_settings.cache_clear()

            gate = resolve_chat_turn(
                "check railway execution readiness",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(gate, route_id="railway_execution_contract")
            assert gate.intent == "railway_execution_readiness_gate"
            assert gate.meta.get("mutation_performed") == "false"

            execute = resolve_chat_turn(
                "execute railway service creation",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(execute, route_id="railway_execution_contract")
            assert execute.intent == "railway_execution_contract_requested"
            assert execute.meta.get("mutation_performed") == "false"
            assert execute.meta.get("real_mutation_allowed") == "false"
            assert int(execute.meta.get("simulated_phase_count") or "0") > 0

            timeline = resolve_chat_turn(
                "show railway execution timeline",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(timeline, route_id="railway_execution_contract")
            assert timeline.intent == "railway_execution_timeline"
            assert "# Railway Execution Timeline" in timeline.reply
            assert "Mutation performed:" in timeline.reply

            receipts_turn = resolve_chat_turn(
                "show railway execution receipts",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(receipts_turn, route_id="railway_execution_contract")
            assert receipts_turn.intent == "railway_execution_contract_receipts"
            assert receipts_turn.meta.get("mutation_performed") == "false"
            assert "mutation_performed: **false**" in receipts_turn.reply

            plan_ctx = get_deployment_plan_context(session_id=session) or {}
            execution_id = resolve_execution_id_for_plan(session_id=session, plan=plan_ctx)
            assert execution_id
            receipts = list_execution_receipts(execution_id=execution_id)
            assert receipts, "dry-run execute must persist receipts"
            assert all(r.get("mutation_performed") is False for r in receipts)


class TestStabilityContractBrowserLane:
    @patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
    @patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=False)
    def test_browser_screenshot_route_unchanged(self, _ready, mock_inspect) -> None:
        mock_inspect.return_value = {
            "canonical_env_var": "BROWSER_AUTOMATION_ENABLED",
            "execution_ready": False,
            "chromium_binary_installed": False,
            "browser_launch_test": "fail",
            "remediation_notes": [],
            "recommended_install_commands": [],
        }
        result = resolve_chat_turn(
            "take a screenshot of pilotmain.com",
            session_id="stability-browser-v1",
            apply_relational_layer=False,
        )
        assert_route_owns(result, route_id="browser_observation", intent="browser_observation_blocked")
        assert_no_generic_capability_prose(result)

    def test_show_route_trace_unchanged(self) -> None:
        session = "stability-trace-v1"
        save_last_route_trace(
            session_id=session,
            meta={
                "route_id": "browser_observation",
                "matched_module": "browser_observation_router",
                "route_trace": "browser_observation → browser_observation_blocked",
            },
        )
        result = resolve_chat_turn("show route trace", session_id=session, apply_relational_layer=False)
        assert result.intent == "internal_route_trace_diagnostics"
        assert result.meta.get("scope") == "internal_diagnostics"
        assert "browser_observation" in result.reply
        assert_no_generic_capability_prose(result)


class TestStabilityContractGitHubWorkflowLane:
    def test_workflow_lane_proposal_creation_push_blocked_cancel(self) -> None:
        session = "stability-github-v1"
        proposal = route_workflow_lane("draft workflow proposal", session_id=session)
        assert proposal is not None
        assert proposal[1] == "workflow_discovery_proposal"
        assert proposal[2]["route_id"] == "github_workflow_lane"

        creation = route_workflow_lane("create this workflow file", session_id=session)
        assert creation is not None
        assert creation[1] == "workflow_creation_governed_plan"
        assert creation[2]["route_id"] == "github_workflow_lane"
        assert "No file, branch, commit, push, or PR" not in creation[0]

        push = route_workflow_lane("push the workflow to main", session_id=session)
        assert push is not None
        assert push[2]["route_id"] == "github_workflow_lane"
        assert "will not" in push[0] or "blocked" in push[0].lower()
        assert "T3" in push[0]

        cancel = route_workflow_lane("cancel", session_id=session)
        assert cancel is not None
        assert cancel[1] == "workflow_creation_cancelled"
        assert cancel[2]["route_id"] == "github_workflow_lane"

    def test_resolve_chat_turn_workflow_not_railway_plan(self) -> None:
        result = resolve_chat_turn(
            "draft workflow proposal",
            session_id="stability-gh-isolation",
            apply_relational_layer=False,
        )
        assert_route_owns(result, route_id="github_workflow_lane")
        assert_route_did_not_call_provider(result, "railway")


class TestStabilityContractRailwayRestartLane:
    def test_restart_not_deployment_plan_or_execution_contract(self) -> None:
        with _resolved_railway_gate():
            result = resolve_chat_turn(
                "restart pilotos-api in railway",
                session_id="stability-restart-v1",
                apply_relational_layer=False,
            )
        assert_no_generic_capability_prose(result)
        assert_route_did_not_call_provider(result, "github")
        assert result.intent in {
            "mutation_preflight_job_created",
            "explicit_mutation_preflight",
            "mutation_target_clarification",
        }
        assert str(result.meta.get("route_id") or "") != "railway_deployment_plan"
        assert str(result.meta.get("route_id") or "") != "railway_execution_contract"
        assert "governed new-service plan" not in result.reply.lower()
