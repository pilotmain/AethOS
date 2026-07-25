# SPDX-License-Identifier: Apache-2.0
"""AethOS core regression certification — live routing entrypoints only.

Run: pytest tests/certification/test_aethos_core_certification.py
Or:  make certify
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch

import pytest

from aethos_core.chat.cognition_exception_boundary import safe_resolve_operational_turn
from aethos_core.chat.handlers import resolve_handler
from aethos_core.chat.route_trace import save_last_route_trace
from aethos_core.chat.service import resolve_chat_turn, resolve_deterministic_turn
from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.providers.github.workflow_lane.workflow_lane_lifecycle import persist_workflow_lane_state
from aethos_core.providers.github.workflow_lane.workflow_lane_router import (
    clear_memory_cache_for_tests,
    get_workflow_lane_state,
    route_workflow_lane,
)
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.runtime.jobs import job_store
from aethos_core.task_frame.pending_action import PendingAction, store_pending_action
from aethos_core.task_frame.clarification_state import store_target_selection_task
from tests.certification.helpers import (
    assert_json_payload_valid,
    assert_no_generic_capability_prose,
    assert_route_did_not_call_provider,
    assert_route_owns,
    reset_certification_runtime,
)

pytestmark = pytest.mark.certification


@pytest.fixture(autouse=True)
def _cert_clean():
    reset_certification_runtime()
    yield
    reset_certification_runtime()


@contextmanager
def _resolved_railway_gate(*, service: str = "pilotos-api", project: str = "pilotos"):
    def _gate(text, params, operation_type):
        _ = text, operation_type
        enriched = {
            **params,
            "target_name": service,
            "target_resolved": True,
            "target": {
                "project_name": project,
                "environment": "production",
                "service_name": service,
                "resolved": True,
            },
        }
        return enriched, None

    binding = type("Binding", (), {"ok": True, "stored_github_repo": "", "referenced_github_repo": ""})()
    with patch("aethos_core.chat.mutation_target_chat.gate_railway_mutation_preflight", side_effect=_gate), patch(
        "aethos_core.provider_topology.binding_verifier.verify_source_binding",
        return_value=binding,
    ):
        yield


def _mongo_health_rows() -> list[dict]:
    return [
        {
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
            "service_id": "svc-mongo",
        },
        {
            "service": "pilotos-api",
            "project": "pilotos",
            "environment": "production",
            "status": "running",
            "health": "healthy",
            "service_id": "svc-api",
        },
    ]


def _provider_wide_rows() -> list[dict]:
    return [
        {"service": "pilotos-api", "project": "pilotos", "environment": "production", "status": "running", "health": "healthy"},
        {"service": "MongoDB", "project": "pilotcore-sales-engine", "environment": "production", "status": "failed", "health": "failed"},
        {"service": "api", "project": "atlas-trader", "environment": "production", "status": "running", "health": "healthy"},
    ]


def _blocked_workflow_state() -> dict:
    return {
        "repo": "pilotmain/aethos",
        "file_path": ".github/workflows/ci.yml",
        "base_branch": "main",
        "branch": "add-ci-workflow",
        "proposal_yaml": "name: CI\n",
        "stage": "execution_blocked",
        "blocker": "missing_github_mutation_credential",
        "last_failed_step": "credential_resolution",
        "branch_created": False,
        "file_committed": False,
        "pr_opened": False,
        "workflow_run_triggered": False,
        "execution_attempts": 1,
    }


# ─── 1. Railway Restart ──────────────────────────────────────────────────────


class TestRailwayRestartCertification:
    def test_restart_preflight_no_github_discovery_error(self) -> None:
        outcome = run_mutation_preflight(
            job_type="mutation_preflight",
            params={
                "provider": "railway",
                "operation_type": "restart",
                "user_request": "restart pilotos-api in railway",
                "target_name": "pilotos-api",
                "target_resolved": True,
                "target": {
                    "provider": "railway",
                    "project_name": "pilotos",
                    "environment": "production",
                    "service_name": "pilotos-api",
                    "resolved": True,
                },
                "session_id": "cert-railway-preflight",
            },
        )
        assert "discovery" not in outcome.summary.lower()
        assert outcome.provider == "railway"

    @patch("aethos_core.runtime.authority.authority.create_job")
    def test_target_selection_creates_railway_preflight(self, mock_create_job) -> None:
        import secrets

        mock_create_job.return_value = type("Job", (), {"id": f"job-{secrets.token_hex(6)}"})()
        session = "cert-railway-select"
        store_target_selection_task(
            session_id=session,
            provider="railway",
            operation="restart",
            original_request="restart pilotos-api in railway",
            candidates=[
                {"project_name": "atlas-trader", "environment": "production", "service_name": "api", "service_id": "svc-1"},
                {"project_name": "lifeos", "environment": "production", "service_name": "api", "service_id": "svc-2"},
                {
                    "project_name": "pilotos",
                    "environment": "production",
                    "service_name": "pilotos-api",
                    "service_id": "svc-pilotos-api",
                },
            ],
        )
        with _resolved_railway_gate():
            selected = resolve_chat_turn(
                "3. pilotos / production / pilotos-api",
                session_id=session,
                apply_relational_layer=False,
            )
        assert selected.intent == "task_frame_preflight_created", selected.intent
        assert_route_did_not_call_provider(selected, "github")
        assert "pilotos-api" in selected.reply
        assert "preflight" in selected.reply.lower()

    def test_restart_intent_via_resolve_chat_turn(self) -> None:
        with _resolved_railway_gate():
            restart = resolve_chat_turn(
                "restart pilotos-api in railway",
                session_id="cert-railway-restart-only",
                apply_relational_layer=False,
            )
        assert_route_did_not_call_provider(restart, "github")
        assert_no_generic_capability_prose(restart)
        assert restart.intent in {
            "mutation_preflight_job_created",
            "explicit_mutation_preflight",
            "mutation_target_clarification",
        }

    @patch("aethos_core.task_frame.confirmation_continuation.create_governed_retry_preflight")
    def test_retry_routes_railway_not_github(self, mock_retry) -> None:
        mock_retry.return_value = (
            "Retrying the latest Railway restart preflight for pilotos / production / pilotos-api.",
            "pending_action_preflight_created",
            {"provider": "railway", "route_id": "retry_active_operation"},
        )
        store_pending_action(
            PendingAction(
                session_id="cert-railway-retry",
                provider="railway",
                project="pilotos",
                environment="production",
                service="pilotos-api",
                operation="restart",
                next_action="create_mutation_preflight",
                status="awaiting_user_confirmation",
            ),
        )
        result = resolve_chat_turn("retry", session_id="cert-railway-retry", apply_relational_layer=False)
        assert "Railway" in result.reply
        assert_route_did_not_call_provider(result, "github")
        assert "No pending GitHub workflow creation plan" not in result.reply


# ─── 2. GitHub Workflow Lane ─────────────────────────────────────────────────


class TestGitHubWorkflowLaneCertification:
    def test_proposal_creation_approve_followups_cancel(self) -> None:
        session = "cert-github-lane"
        proposal = route_workflow_lane("draft workflow proposal", session_id=session)
        assert proposal is not None
        body, intent, meta = proposal
        assert intent == "workflow_discovery_proposal"
        assert "```yaml" in body
        assert "name: CI" in body
        assert meta["route_id"] == "github_workflow_lane"

        creation = route_workflow_lane("create this workflow file", session_id=session)
        assert creation is not None
        c_body, c_intent, c_meta = creation
        assert c_intent == "workflow_creation_governed_plan"
        assert "governed workflow-file creation plan" in c_body
        assert "branch" in c_body.lower() and "pr" in c_body.lower()
        assert c_meta["workflow_lane_stage"] == "creation_plan_ready"

        state = get_workflow_lane_state(session_id=session) or {}
        persist_workflow_lane_state(
            session,
            {
                **state,
                "stage": "execution_blocked",
                "blocker": "missing_github_mutation_credential",
                "pr_opened": False,
            },
        )
        pr = route_workflow_lane("did the PR open?", session_id=session)
        assert pr is not None
        assert pr[1] == "workflow_execution_blocked_followup"
        assert "PR" in pr[0] or "pr" in pr[0].lower()

        cred = route_workflow_lane("what credential is missing?", session_id=session)
        assert cred is not None
        assert "credential" in cred[0].lower() or "token" in cred[0].lower()

        cancel = route_workflow_lane("cancel", session_id=session)
        assert cancel is not None
        assert cancel[1] == "workflow_creation_cancelled"

    def test_resolve_chat_turn_workflow_lane_not_railway_thread(self) -> None:
        result = resolve_chat_turn("draft workflow proposal", session_id="cert-gh-hijack", apply_relational_layer=False)
        assert result.intent == "workflow_discovery_proposal"
        assert_route_owns(result, route_id="github_workflow_lane")
        assert_route_did_not_call_provider(result, "railway")
        assert_route_did_not_call_provider(result, "active_thread")


# ─── 3. Browser Screenshot ───────────────────────────────────────────────────


class TestBrowserScreenshotCertification:
    @patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
    @patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=False)
    def test_routes_browser_observation_blocked_exactly(self, _ready, mock_inspect) -> None:
        mock_inspect.return_value = {
            "canonical_env_var": "BROWSER_AUTOMATION_ENABLED",
            "ignored_env_vars": ["PLAYWRIGHT_ENABLED", "BROWSER_ENABLED"],
            "env_flag_loaded": True,
            "settings_value": True,
            "playwright_python_package_installed": True,
            "chromium_binary_installed": False,
            "browser_launch_test": "fail (Chromium missing)",
            "worker_enabled": True,
            "execution_ready": False,
            "remediation_notes": [],
            "recommended_install_commands": [],
        }
        result = resolve_chat_turn(
            "take a screenshot of pilotmain.com",
            session_id="cert-browser",
            apply_relational_layer=False,
        )
        assert_route_owns(result, route_id="browser_observation", intent="browser_observation_blocked")
        assert "Runtime checks (this API process):" in result.reply
        assert "chromium binary installed: no" in result.reply
        assert "Playwright runtime unavailable" not in result.reply
        assert_no_generic_capability_prose(result)
        assert_route_did_not_call_provider(result, "github")
        assert_route_did_not_call_provider(result, "railway")

    @patch("aethos_core.browser.runtime.browser_runtime.run_browser_evidence_capture")
    @patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=True)
    @patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
    def test_capture_success_when_runtime_ready(self, mock_inspect, _ready, mock_capture) -> None:
        mock_inspect.return_value = {"execution_ready": True, "browser_launch_test": "pass"}
        mock_capture.return_value = {
            "ok": True,
            "summary": "Browser evidence captured",
            "artifacts": [{"artifact_id": "bart-cert-1", "artifact_type": "browser_screenshot"}],
        }
        result = resolve_chat_turn(
            "take a screenshot of pilotmain.com",
            session_id="cert-browser-ok",
            apply_relational_layer=False,
        )
        assert result.intent == "browser_observation_captured"
        assert "Screenshot captured" in result.reply
        assert_no_generic_capability_prose(result)

    @patch("aethos_core.browser.runtime.browser_runtime.run_browser_evidence_capture")
    @patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=True)
    @patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
    def test_browser_observation_lifecycle_followups(self, mock_inspect, _ready, mock_capture) -> None:
        mock_inspect.return_value = {
            "execution_ready": True,
            "browser_launch_test": "pass",
            "env_flag_loaded": True,
            "playwright_python_package_installed": True,
            "chromium_binary_installed": True,
            "worker_enabled": True,
        }
        mock_capture.return_value = {
            "ok": True,
            "summary": "Browser evidence captured",
            "artifacts": [
                {
                    "artifact_id": "bart-19f5d290be01",
                    "artifact_type": "browser_screenshot",
                    "artifact_file_url": "/api/v1/browser/artifacts/bart-19f5d290be01/file",
                },
            ],
        }
        session = "cert-browser-lifecycle"
        capture = resolve_chat_turn(
            "take a screenshot of pilotmain.com",
            session_id=session,
            apply_relational_layer=False,
        )
        assert capture.intent == "browser_observation_captured"
        assert capture.meta.get("artifact_id") == "bart-19f5d290be01"

        show = resolve_chat_turn("show me the screenshot", session_id=session, apply_relational_layer=False)
        assert show.intent == "browser_observation_show_artifact"
        assert "bart-19f5d290be01" in show.reply
        assert "/api/v1/browser/artifacts/bart-19f5d290be01/file" in show.reply
        assert show.meta.get("browser_observation_hydrated") == "true"
        assert_no_generic_capability_prose(show)

        where = resolve_chat_turn("where is the screenshot saved?", session_id=session, apply_relational_layer=False)
        assert where.intent == "browser_observation_artifact_location"
        assert "browser observation artifact" in where.reply.lower()
        assert "bart-19f5d290be01" in where.reply

        cap = resolve_chat_turn(
            "are you capable of taking screenshots?",
            session_id=session,
            apply_relational_layer=False,
        )
        assert cap.intent == "browser_observation_capability"
        assert "available and operational" in cap.reply.lower()
        assert "pilotmain.com" in cap.reply
        assert_route_did_not_call_provider(cap, "browser_observation")
        assert "cannot take screenshots" not in cap.reply.lower()


# ─── 3b. Railway New-Service Deployment Readiness ─────────────────────────────


class TestRailwayDeploymentReadinessCertification:
    @patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks"
    )
    def test_new_service_capability_truth(self, mock_checks) -> None:
        mock_checks.return_value = {
            "readonly_readiness_ok": True,
            "inventory": {"ok": True, "project_count": 1, "environment_count": 1, "service_count": 1, "projects": []},
            "github_binding": {"github_credential_ok": True, "accessible_repos_count": 1},
            "service_creation": {"governed_mutation_adapter_ops": ["restart", "redeploy"], "env_var_writes_enabled": False},
            "required_env_vars": ["RAILWAY_API_TOKEN"],
            "execution_mode": "api",
        }
        result = resolve_chat_turn(
            "can you deploy a brand new railway service?",
            session_id="cert-railway-new-svc",
            apply_relational_layer=False,
        )
        assert_route_owns(result, route_id="railway_deployment_readiness")
        assert "existing" in result.reply.lower() and "railway services" in result.reply.lower()
        assert "readiness checks first" in result.reply.lower()
        assert "no service will be created until" in result.reply.lower()
        assert_no_generic_capability_prose(result)

    @patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.run_deployment_readiness_checks"
    )
    def test_readiness_report_not_github_lane(self, mock_checks) -> None:
        mock_checks.return_value = {
            "readonly_readiness_ok": False,
            "railway_credential_ok": False,
            "railway_api_connection_ok": False,
            "railway_credential_source": "none",
            "execution_mode": "api",
            "required_env_vars": ["RAILWAY_API_TOKEN"],
            "inventory": {"ok": False, "project_count": 0, "environment_count": 0, "service_count": 0, "projects": []},
            "github_binding": {"github_credential_ok": False, "accessible_repos_count": 0},
            "service_creation": {
                "graphql_service_create": False,
                "graphql_service_create_detail": "not wired",
                "governed_mutation_adapter_ops": ["restart", "redeploy"],
                "env_var_writes_enabled": False,
            },
        }
        result = resolve_chat_turn(
            "run railway deployment readiness",
            session_id="cert-railway-readiness",
            apply_relational_layer=False,
        )
        assert result.intent in {
            "railway_deployment_readiness",
            "railway_deployment_readiness_blocked",
            "railway_deployment_readiness_passed_not_mutation_ready",
        }
        assert (
            "Railway new-service deployment readiness" in result.reply
            or "one readonly check failed" in result.reply.lower()
            or "readiness checks passed" in result.reply.lower()
        )
        assert "internal error" not in result.reply.lower()
        assert_no_generic_capability_prose(result)


# ─── 3b. Railway Env Value Readiness ────────────────────────────────────────────


class TestRailwayEnvValueReadinessCertification:
    @patch("aethos_core.credentials.get_provider_api_token")
    def test_env_value_readiness_and_simulator_reflect_secure_state(self, mock_token, monkeypatch) -> None:
        monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        from aethos_core.providers.railway.deployment_plan.creation_preflight import (
            build_creation_preflight_from_plan,
        )
        from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
            save_creation_preflight,
        )
        from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
            save_deployment_plan_context,
        )
        from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation

        mock_token.return_value = None
        plan = apply_plan_review_confirmation(
            {
                "repo": "pilotmain/aethos",
                "branch": "main",
                "project": "pilotos",
                "environment": "production",
                "service_name": "aethos-api",
                "runtime": "Python",
                "build_command": "pip install -r requirements.txt",
                "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
                "health_check_path": "/api/v1/health",
                "required_env_var_names": ["APP_ENV", "API_PORT", "OPENAI_API_KEY"],
                "mutation_ready": True,
            }
        )
        session = "cert-env-value-99"
        save_deployment_plan_context(session_id=session, plan=plan)
        save_creation_preflight(session_id=session, preflight=build_creation_preflight_from_plan(plan))

        check = resolve_chat_turn(
            "check railway env value readiness",
            session_id=session,
            apply_relational_layer=False,
        )
        assert_route_owns(check, route_id="railway_env_value_readiness")
        assert "OPENAI_API_KEY" in check.reply
        assert "sk-" not in check.reply.lower()
        assert "No secret values should be pasted" in check.reply or "No secret values" in check.reply

        guide = resolve_chat_turn(
            "how do I configure env values securely?",
            session_id=session,
            apply_relational_layer=False,
        )
        assert_route_owns(guide, route_id="railway_env_value_readiness")
        assert "Credential Center" in guide.reply
        assert guide.meta.get("mutation_performed") == "false"

        sim = resolve_chat_turn(
            "simulate railway service creation",
            session_id=session,
            apply_relational_layer=False,
        )
        assert_route_owns(sim, route_id="railway_service_creation_simulator")
        assert "env_values_not_configured" in (sim.meta.get("blocking_reasons") or "")
        assert "greenfield_service_creation_not_wired" in (sim.meta.get("blocking_reasons") or "")
        assert "No mutation has been performed" in sim.reply

    @patch("aethos_core.credentials.get_provider_api_token")
    def test_optional_env_vars_do_not_block_when_critical_secrets_present(self, mock_token, monkeypatch) -> None:
        monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        from aethos_core.providers.railway.deployment_plan.creation_preflight import (
            build_creation_preflight_from_plan,
        )
        from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
            save_creation_preflight,
        )
        from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
            save_deployment_plan_context,
        )
        from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation

        mock_token.return_value = "cert-token"
        plan = apply_plan_review_confirmation(
            {
                "repo": "pilotmain/aethos",
                "branch": "main",
                "project": "pilotos",
                "environment": "production",
                "service_name": "aethos-api",
                "runtime": "Python",
                "build_command": "pip install -r requirements.txt",
                "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
                "health_check_path": "/api/v1/health",
                "required_env_var_names": [
                    "APP_ENV",
                    "API_PORT",
                    "ANTHROPIC_API_KEY",
                    "WEB_SEARCH_API_KEY",
                    "TELEGRAM_TYPING_INTERVAL_SECONDS",
                    "LOCAL_WORKSPACE_ARTIFACTS_DIR",
                ],
                "mutation_ready": True,
            }
        )
        session = "cert-env-value-99b"
        save_deployment_plan_context(session_id=session, plan=plan)
        save_creation_preflight(session_id=session, preflight=build_creation_preflight_from_plan(plan))

        check = resolve_chat_turn(
            "check railway env value readiness",
            session_id=session,
            apply_relational_layer=False,
        )
        assert_route_owns(check, route_id="railway_env_value_readiness")
        assert check.meta.get("env_value_ready") == "true"
        assert "cert-token" not in check.reply

        sim = resolve_chat_turn(
            "simulate railway service creation",
            session_id=session,
            apply_relational_layer=False,
        )
        assert_route_owns(sim, route_id="railway_service_creation_simulator")
        blocking = sim.meta.get("blocking_reasons") or ""
        assert "env_values_not_configured" not in blocking
        assert "greenfield_service_creation_not_wired" in blocking

        blocking_turn = resolve_chat_turn(
            "what is blocking execution?",
            session_id=session,
            apply_relational_layer=False,
        )
        assert "greenfield" in blocking_turn.reply.lower() or "not wired" in blocking_turn.reply.lower()
        assert "cert-token" not in blocking_turn.reply


# ─── 3c. Railway Service Creation Simulator ───────────────────────────────────


class TestRailwayServiceCreationSimulatorCertification:
    @patch(
        "aethos_core.providers.railway.service_creation_simulator.simulator_checks.run_all_simulator_checks"
    )
    def test_simulator_flow_after_plan_and_preflight(self, mock_checks, monkeypatch) -> None:
        monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        from aethos_core.providers.railway.deployment_plan.creation_preflight import (
            build_creation_preflight_from_plan,
        )
        from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
            save_creation_preflight,
        )
        from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
            save_deployment_plan_context,
        )
        from aethos_core.providers.railway.deployment_plan.plan_review import apply_plan_review_confirmation

        mock_checks.return_value = [
            {"check": "railway_project_environment", "status": "pass", "details": "ok"},
            {"check": "service_name_availability", "status": "pass", "details": "ok"},
            {"check": "github_source_binding", "status": "pass", "details": "ok"},
            {"check": "railway_credential_readiness", "status": "pass", "details": "ok"},
            {
                "check": "required_env_var_readiness",
                "status": "blocked",
                "env_var_names_status": "pass",
                "env_var_values_status": "blocked",
                "details": "values not configured",
            },
            {"check": "build_start_health_readiness", "status": "pass", "details": "ok"},
            {"check": "rollback_readiness", "status": "pass", "details": "ok"},
            {"check": "execution_api_surface", "status": "blocked", "details": "not wired"},
        ]
        plan = apply_plan_review_confirmation(
            {
                "repo": "pilotmain/aethos",
                "branch": "main",
                "project": "pilotos",
                "environment": "production",
                "service_name": "aethos-api",
                "runtime": "Python",
                "build_command": "pip install -r requirements.txt",
                "start_command": "uvicorn main:app --host 0.0.0.0 --port $PORT",
                "health_check_path": "/api/v1/health",
                "required_env_var_names": ["APP_ENV"],
                "mutation_ready": True,
            }
        )
        session = "cert-railway-sim-98"
        save_deployment_plan_context(session_id=session, plan=plan)
        save_creation_preflight(session_id=session, preflight=build_creation_preflight_from_plan(plan))
        result = resolve_chat_turn(
            "simulate railway service creation",
            session_id=session,
            apply_relational_layer=False,
        )
        assert_route_owns(result, route_id="railway_service_creation_simulator")
        assert result.meta.get("ready_to_execute") == "false"
        assert result.meta.get("mutation_performed") == "false"
        assert "ready_to_execute: false" in result.reply
        assert "No service has been created" in result.reply
        assert "No mutation has been performed" in result.reply
        assert_no_generic_capability_prose(result)


# ─── 4. Provider-Wide Railway Health ─────────────────────────────────────────


class TestProviderWideRailwayHealthCertification:
    def test_check_all_services_table_json_rerender(self) -> None:
        from aethos_core.operational_planner.planner_router import compose_planned_operational_reply

        session = "cert-provider-wide"
        rows = _provider_wide_rows()
        with patch(
            "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
            return_value=(rows, None),
        ):
            initial_body, initial_intent, initial_meta = compose_planned_operational_reply(
                "check all services in railway",
                session_id=session,
            )
        assert initial_intent is not None
        assert "MongoDB" in initial_body or "failed" in initial_body.lower()

        failed_body, failed_intent, _failed_meta = compose_planned_operational_reply(
            "show only failed",
            session_id=session,
        )
        assert failed_intent is not None
        assert "MongoDB" in failed_body
        assert "pilotos-api" not in failed_body.split("Failed services:")[-1] if "Failed services:" in failed_body else True

        table_body, table_intent, _table_meta = compose_planned_operational_reply(
            "table format please",
            session_id=session,
        )
        assert table_intent is not None
        assert "|" in table_body or "table" in table_body.lower()

        json_body, json_intent, _json_meta = compose_planned_operational_reply("json", session_id=session)
        assert json_intent is not None
        payload = assert_json_payload_valid(json_body)
        assert "services" in payload or "failures" in payload or "counts" in payload

        with _resolved_railway_gate():
            via_chat = resolve_chat_turn(
                "check all services in railway",
                session_id="cert-provider-wide-chat",
                apply_relational_layer=False,
            )
        assert_route_did_not_call_provider(via_chat, "active_thread")
        assert "failed" in via_chat.reply.lower() or "MongoDB" in via_chat.reply


# ─── 5. MongoDB Investigation ──────────────────────────────────────────────


class TestMongoDBInvestigationCertification:
    def _mock_logs(self):
        return patch(
            "aethos_core.failed_service_investigation.failed_service_diagnosis.fetch_railway_logs_multisource",
            return_value={
                "ok": True,
                "logs": [{"timestamp": "2026-05-20T01:00:00Z", "message": "connection refused"}],
                "sources_checked": ["deployment_logs"],
                "errors": [],
                "all_sources_failed": False,
            },
        )

    def test_failed_service_flow_no_vercel_hijack(self) -> None:
        session = "cert-mongo"
        store_provider_wide_health_result(
            session_id=session,
            provider="railway",
            payload={
                "services": _mongo_health_rows(),
                "counts": {"total": 2, "failed": 1, "healthy": 1},
                "failures": [_mongo_health_rows()[0]],
                "unknown": [],
            },
            summary={"total": 2, "failed": 1, "healthy": 1},
        )
        with self._mock_logs():
            why = resolve_chat_turn("why is MongoDB failed?", session_id=session, apply_relational_layer=False)
        assert why.intent == "failed_service_diagnosis"
        assert_route_did_not_call_provider(why, "vercel")
        assert "MongoDB" in why.reply

        with self._mock_logs(), patch(
            "aethos_core.world_model.guided_evidence_orchestrator.can_execute_readonly_guided_evidence",
            return_value=(True, ""),
        ), patch(
            "aethos_core.providers.railway.operations.service_events_api.get_service_events",
            return_value={"ok": True, "events": []},
        ), patch(
            "aethos_core.world_model.investigation_strategy_router.compose_investigation_strategy_route_reply",
        ) as strat:
            strat.return_value = (
                "Next I would inspect events read-only; I would not recommend another restart yet.",
                "investigation_strategy",
                {"route_id": "investigation_strategy"},
            )
            nxt = resolve_chat_turn("what should we do next?", session_id=session, apply_relational_layer=False)
        assert "restart" in nxt.reply.lower() or "investigat" in nxt.reply.lower()
        assert_route_did_not_call_provider(nxt, "vercel")

        did_help = resolve_chat_turn("did restart help?", session_id=session, apply_relational_layer=False)
        assert_route_did_not_call_provider(did_help, "vercel")

        again = resolve_chat_turn("should we restart again?", session_id=session, apply_relational_layer=False)
        assert_route_did_not_call_provider(again, "vercel")


# ─── 6. Front Door ───────────────────────────────────────────────────────────


class TestFrontDoorCertification:
    def test_hi_capabilities_help_no_operational_leakage(self) -> None:
        hi = resolve_chat_turn("Hi", session_id="cert-front-hi", apply_relational_layer=False)
        assert hi.intent == "casual_greeting"
        assert_route_did_not_call_provider(hi, "github", allow_markers=())
        assert "mongodb" not in hi.reply.lower()
        assert "railway" not in hi.reply.lower()

        caps = resolve_chat_turn("what are you capable of?", session_id="cert-front-caps", apply_relational_layer=False)
        assert caps.intent in {
            "capability_intro",
            "capability_truth",
            "mission_control_capability_registry_runtime_integration",
        }
        assert "mongodb" not in caps.reply.lower()
        assert "restart pilotos-api" not in caps.reply.lower()

        help_turn = resolve_chat_turn("help", session_id="cert-front-help", apply_relational_layer=False)
        assert help_turn.intent == "general_help"
        assert "mongodb" not in help_turn.reply.lower()
        assert "github workflow" not in help_turn.reply.lower()


# ─── 7. Route Trace ──────────────────────────────────────────────────────────


class TestRouteTraceCertification:
    def test_show_route_trace_reflects_latest_turn(self) -> None:
        session = "cert-route-trace"
        save_last_route_trace(
            session_id=session,
            meta={
                "route_id": "failed_service_preemption",
                "matched_module": "failed_service_investigation.global_preemption",
                "matched_target": "pilotcore-sales-engine / production / MongoDB",
                "blocked_routes": "vercel_why_down,generic_fix_plan",
                "route_trace": "failed_service_preemption → failed_service_diagnosis",
            },
            intent="failed_service_diagnosis",
        )
        result = resolve_chat_turn("show route trace", session_id=session, apply_relational_layer=False)
        assert result.intent == "internal_route_trace_diagnostics"
        assert "failed_service_preemption" in result.reply
        assert "matched_module" in result.reply.lower() or "failed_service_investigation" in result.reply
        assert "blocked_routes" in result.reply.lower() or "vercel_why_down" in result.reply


# ─── 8. Restart Hydration ────────────────────────────────────────────────────


class TestRestartHydrationCertification:
    @patch("aethos_core.operations.orchestration.provider_runtime.resolve_execution_auth", lambda **kw: {})
    @patch("aethos_core.operations.orchestration.provider_runtime.get_provider_api_token", lambda **kw: None)
    def test_durable_workflow_followups_after_memory_clear(self) -> None:
        persist_workflow_lane_state("cert-old-session", _blocked_workflow_state())
        clear_memory_cache_for_tests()

        pr = resolve_chat_turn(
            "did the PR open?",
            session_id="cert-new-session-after-restart",
            apply_relational_layer=False,
        )
        assert pr.intent == "workflow_execution_blocked_followup"
        assert_route_did_not_call_provider(pr, "active_thread")
        assert_no_generic_capability_prose(pr)

        failed = resolve_chat_turn("what failed?", session_id="cert-new-session-after-restart", apply_relational_layer=False)
        assert "credential" in failed.reply.lower() or "failed" in failed.reply.lower()
        assert_route_did_not_call_provider(failed, "active_thread")

        safe = resolve_chat_turn(
            "can we safely retry?",
            session_id="cert-new-session-after-restart",
            apply_relational_layer=False,
        )
        assert "retry" in safe.reply.lower()
        assert_route_did_not_call_provider(safe, "active_thread")

        recap = resolve_chat_turn(
            "what were we doing earlier?",
            session_id="cert-new-session-after-restart",
            apply_relational_layer=False,
        )
        assert recap.intent in {
            "workflow_execution_blocked_followup",
            "operational_narrative_continuity",
            "workflow_lane_blocked_followup",
        }
        assert_route_did_not_call_provider(recap, "active_thread")


# ─── Entrypoint parity ───────────────────────────────────────────────────────


class TestEntrypointParityCertification:
    def test_safe_resolve_operational_turn_browser_observation(self) -> None:
        with patch(
            "aethos_core.browser_observation.browser_observation_router._runtime_is_ready",
            return_value=False,
        ), patch(
            "aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime",
            return_value={
                "canonical_env_var": "BROWSER_AUTOMATION_ENABLED",
                "env_flag_loaded": False,
                "playwright_python_package_installed": False,
                "chromium_binary_installed": False,
                "browser_launch_test": "skipped",
                "worker_enabled": True,
                "remediation_notes": [],
                "recommended_install_commands": [],
            },
        ):
            result = safe_resolve_operational_turn(
                "take a screenshot of pilotmain.com",
                session_id="cert-safe-resolve",
            )
        assert result is not None
        assert result.intent == "browser_observation_blocked"

    def test_resolve_handler_and_deterministic_do_not_generic_fallback(self) -> None:
        with patch(
            "aethos_core.browser_observation.browser_observation_router._runtime_is_ready",
            return_value=False,
        ), patch(
            "aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime",
            return_value={
                "canonical_env_var": "BROWSER_AUTOMATION_ENABLED",
                "env_flag_loaded": True,
                "playwright_python_package_installed": False,
                "chromium_binary_installed": False,
                "browser_launch_test": "fail",
                "worker_enabled": False,
                "remediation_notes": [],
                "recommended_install_commands": [],
            },
        ):
            handled = resolve_handler("take a screenshot of pilotmain.com", session_id="cert-handler")
            assert handled is not None
            reply, intent, _meta = handled
            assert intent == "browser_observation_blocked"
            assert "How I can help" not in reply

            det = resolve_deterministic_turn("take a screenshot of pilotmain.com", session_id="cert-det")
        if det is not None:
            assert "How I can help" not in det.reply
