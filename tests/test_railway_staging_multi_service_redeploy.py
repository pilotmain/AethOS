# SPDX-License-Identifier: Apache-2.0
"""Railway staging multi-service redeploy target resolution and follow-ups."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.provider_e2e_execution.railway_e2e_execution import (
    _pick_target_services,
    route_railway_e2e_execution,
)
from aethos_core.providers.railway.railway_inventory_target_picker import (
    default_aethos_service_hints,
    extract_environment_hint,
    extract_project_hint,
    extract_service_hints,
    infer_redeploy_environment,
    parse_target_selection_reply,
    pick_railway_targets,
)
from aethos_core.runtime.jobs import job_store
from aethos_core.task_frame.clarification_state import store_target_selection_task
from aethos_core.task_frame.railway_redeploy_intent import (
    clear_railway_redeploy_intents_for_tests,
    save_railway_redeploy_intent,
)
from aethos_core.task_frame.railway_redeploy_continuation import compose_railway_redeploy_continuation_reply
from aethos_core.task_frame.selection_resolver import resolve_selections
from aethos_core.task_frame.task_continuation import compose_task_continuation_reply, is_task_execution_ack
from aethos_core.task_frame.task_memory import clear_task_frames_for_tests, get_active_task_frame


@pytest.fixture(autouse=True)
def _clean():
    get_settings.cache_clear()
    clear_task_frames_for_tests()
    clear_railway_redeploy_intents_for_tests()
    job_store.clear_for_tests()
    yield
    clear_task_frames_for_tests()
    clear_railway_redeploy_intents_for_tests()
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _pilotos_inventory() -> dict:
    staging_services = ["Postgres", "aethos-api", "aethos-ui", "aethos.git-api", "pilotos-api", "Redis"]
    production_services = list(staging_services)
    return {
        "ok": True,
        "project_count": 1,
        "environment_count": 2,
        "service_count": len(staging_services) + len(production_services),
        "projects": [
            {
                "name": "pilotos",
                "environments": [
                    {"name": "staging", "services": staging_services},
                    {"name": "production", "services": production_services},
                ],
            }
        ],
    }


def test_extracts_staging_and_ui_api_hints():
    text = (
        "check AethOS changes in github and redeploy latest commits to railway stage "
        "for both UI and API changes"
    )
    assert extract_environment_hint(text) == "staging"
    hints = extract_service_hints(text)
    assert "aethos-ui" in hints
    assert "aethos-api" in hints


def test_parse_target_selection_reply():
    env, services = parse_target_selection_reply("staging: aethos-api, aethos-ui")
    assert env == "staging"
    assert services == ["aethos-api", "aethos-ui"]


def test_pick_railway_targets_resolves_staging_ui_and_api():
    checks = {"inventory": _pilotos_inventory()}
    text = "redeploy railway staging for both UI and API"
    result = pick_railway_targets(checks, text)
    assert result.reason == "resolved"
    assert len(result.targets) == 2
    services = {row.service for row in result.targets}
    assert services == {"aethos-api", "aethos-ui"}
    assert all(row.environment == "staging" for row in result.targets)


def test_resolve_selections_from_env_service_reply():
    frame = store_target_selection_task(
        session_id="railway-multi",
        provider="railway",
        operation="redeploy",
        original_request="redeploy railway staging for both UI and API",
        candidates=[
            {
                "project_name": "pilotos",
                "environment": "staging",
                "service_name": "aethos-api",
            },
            {
                "project_name": "pilotos",
                "environment": "staging",
                "service_name": "aethos-ui",
            },
            {
                "project_name": "pilotos",
                "environment": "production",
                "service_name": "aethos-api",
            },
        ],
    )
    selected = resolve_selections("staging: aethos-api, aethos-ui", frame)
    assert len(selected) == 2
    assert {row.service for row in selected} == {"aethos-api", "aethos-ui"}


def test_task_continuation_creates_two_preflights(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    store_target_selection_task(
        session_id="railway-flow",
        provider="railway",
        operation="redeploy",
        original_request="redeploy railway staging for both UI and API",
        candidates=[
            {
                "project_name": "pilotos",
                "environment": "staging",
                "service_name": "aethos-api",
            },
            {
                "project_name": "pilotos",
                "environment": "staging",
                "service_name": "aethos-ui",
            },
        ],
        params={"provider": "railway", "operation_type": "redeploy"},
    )
    reply = compose_task_continuation_reply("staging: aethos-api, aethos-ui", session_id="railway-flow")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "task_frame_preflight_created"
    assert meta.get("target_count") == "2"
    assert "aethos-api" in body
    assert "aethos-ui" in body
    assert get_active_task_frame(session_id="railway-flow") is None


def test_execution_ack_phrase_detected():
    assert is_task_execution_ack("redeploying with latest changes?")


def test_route_railway_e2e_multi_target_preflight(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()

    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "inventory": _pilotos_inventory(),
        "required_env_vars": [],
        "service_creation": {"env_var_writes_enabled": False},
    }

    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        lambda **kwargs: checks,
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan.readonly_checks_passed",
        lambda _checks: True,
    )

    body, intent, meta = route_railway_e2e_execution(
        "redeploy railway staging for both UI and API",
        session_id="railway-e2e-multi",
    )
    assert intent == "railway_multi_target_preflight_created"
    assert meta.get("target_count") == "2"
    assert "aethos-api" in body
    assert "aethos-ui" in body


def test_pick_target_services_returns_two_triples():
    checks = {"inventory": _pilotos_inventory()}
    targets = _pick_target_services(checks, user_text="redeploy railway staging for both UI and API")
    assert len(targets) == 2


def test_extracts_pilotos_api_and_ui_paths():
    text = "AethOS in railway pilotos/aethos-api and pilotos/aethos-ui"
    hints = extract_service_hints(text, project_hint="pilotos")
    assert "aethos-api" in hints
    assert "aethos-ui" in hints
    assert extract_project_hint(text) == "pilotos"


def test_pick_targets_prefers_staging_for_git_redeploy():
    checks = {"inventory": _pilotos_inventory()}
    text = "redeploy latest git changes for AethOS in railway pilotos/aethos-api and pilotos/aethos-ui"
    result = pick_railway_targets(checks, text, default_hint="pilotos")
    assert len(result.targets) == 2
    assert all(row.environment == "staging" for row in result.targets)
    assert {row.service for row in result.targets} == {"aethos-api", "aethos-ui"}


def test_lets_do_staging_continuation(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "inventory": _pilotos_inventory(),
        "required_env_vars": [],
        "service_creation": {"env_var_writes_enabled": False},
    }
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        lambda **kwargs: checks,
    )
    save_railway_redeploy_intent(
        __import__(
            "aethos_core.task_frame.railway_redeploy_intent",
            fromlist=["RailwayRedeployIntent"],
        ).RailwayRedeployIntent(
            session_id="railway-staging-followup",
            original_request="redeploy latest git changes for AethOS on railway pilotos/aethos-api and pilotos/aethos-ui",
            project_hint="pilotos",
            service_hints=["aethos-api", "aethos-ui"],
        )
    )
    reply = compose_railway_redeploy_continuation_reply("lets do staging", session_id="railway-staging-followup")
    assert reply is not None
    body, intent, meta = reply
    assert intent == "railway_multi_target_preflight_created"
    assert "aethos-api" in body
    assert "aethos-ui" in body
    assert "staging" in body.lower()
    assert meta.get("target_count") == "2"


def test_redeploying_with_latest_changes_routes_without_llm(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": True,
        "inventory": _pilotos_inventory(),
        "required_env_vars": [],
        "service_creation": {"env_var_writes_enabled": False},
    }
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        lambda **kwargs: checks,
    )
    reply = compose_railway_redeploy_continuation_reply(
        "redeploying with latest changes?",
        session_id="railway-latest-changes",
    )
    assert reply is not None
    body, intent, meta = reply
    assert intent == "railway_multi_target_preflight_created"
    assert "aethos-api" in body
    assert "aethos-ui" in body
    assert "need more context" not in body.lower()
