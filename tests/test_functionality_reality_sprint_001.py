# SPDX-License-Identifier: Apache-2.0
"""FUNCTIONALITY_REALITY_SPRINT_001 regression tests."""

from __future__ import annotations

import pytest

from aethos_core.chat.provider_deploy_capability_intent import route_provider_deploy_capability_reply
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.identity.trust_language import LIGHT_TRUST_REMINDER
from aethos_core.provider_delivery.github_delivery_capability_router import route_github_delivery_capability
from aethos_core.provider_e2e_execution.provider_e2e_execution_intent import is_provider_e2e_execution_intent
from aethos_core.runtime.jobs import job_store

RAILWAY_E2E_PROMPT = "Deploy AethOS to Railway with env vars and verify it."
VERCEL_E2E_PROMPT = "Deploy AethOS to Vercel with env vars and verify it."
RAILWAY_TRUTH_PROMPT = (
    "Can you deploy AethOS to Railway and configure end-to-end environment variables and report back?"
)
GITHUB_DELIVERY_PROMPT = "Create a branch, commit changes, push, and open PR on GitHub."


@pytest.fixture(autouse=True)
def _clear_jobs(monkeypatch):
    from aethos_core.config import get_settings

    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", False)
    job_store.clear_for_tests()
    yield
    job_store.clear_for_tests()


def test_e2e_intent_matcher():
    assert is_provider_e2e_execution_intent(RAILWAY_E2E_PROMPT)
    assert is_provider_e2e_execution_intent(VERCEL_E2E_PROMPT)
    assert is_provider_e2e_execution_intent(RAILWAY_TRUTH_PROMPT)


def test_railway_e2e_chat_route_no_llm():
    result = resolve_chat_turn(RAILWAY_E2E_PROMPT, session_id="sprint-railway-e2e")
    assert result.used_llm is False
    assert result.intent in {
        "railway_e2e_orchestration_preflight",
        "railway_e2e_missing_config",
        "railway_e2e_readiness_blocked",
        "execution_brain_recovery",
        "execution_brain_preflight_created",
        "execution_brain_railway_pilot",
    }
    assert "help plan" not in result.reply.lower()
    assert "***" not in result.reply


def test_vercel_e2e_chat_route_no_llm():
    result = resolve_chat_turn(VERCEL_E2E_PROMPT, session_id="sprint-vercel-e2e")
    assert result.used_llm is False
    assert result.intent in {"vercel_e2e_orchestration_preflight", "vercel_e2e_missing_config"}
    assert "generic planning" not in result.reply.lower()


def test_railway_e2e_missing_config_suppresses_footer(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        lambda: (None, "test", "missing token"),
    )
    result = resolve_chat_turn(RAILWAY_E2E_PROMPT, session_id="sprint-railway-missing", apply_relational_layer=False)
    assert result.intent in {"railway_e2e_missing_config", "execution_brain_recovery"}
    assert LIGHT_TRUST_REMINDER not in result.reply
    if result.intent == "railway_e2e_missing_config":
        assert "missing configuration" in result.reply.lower()
    else:
        assert "not configured" in result.reply.lower() or "token" in result.reply.lower()


def test_github_combined_delivery_truth():
    handled = route_github_delivery_capability(GITHUB_DELIVERY_PROMPT, session_id="sprint-github")
    assert handled is not None
    reply, intent, meta = handled
    assert intent == "github_delivery_capability_truth"
    assert "software delivery" in reply.lower()
    assert "create_branch" in reply.lower() or "disabled" in reply.lower()
    assert meta.get("mutation_performed") == "false"


def test_env_var_mutations_enabled_by_default():
    assert get_settings().provider_env_var_mutations_enabled is True


def test_vercel_adapter_supports_env_mutations_when_enabled():
    from aethos_core.providers.vercel.operations.mutation_adapter import VercelMutationAdapter

    adapter = VercelMutationAdapter()
    assert "set_env_var" in adapter.supported_mutations()
    assert "remove_env_var" in adapter.supported_mutations()


def test_railway_adapter_supports_set_env_when_enabled():
    from aethos_core.providers.railway.operations.mutation_adapter import RailwayMutationAdapter

    adapter = RailwayMutationAdapter()
    assert "set_env_var" in adapter.supported_mutations()


def test_local_workspace_catalog_backend_ready():
    from aethos_core.catalog.connection_catalog import build_connections_catalog

    catalog = build_connections_catalog()
    backend = catalog.get("backend_ready_providers") or []
    local = [p for p in backend if p.get("name") == "local"]
    assert len(local) == 1
    assert local[0].get("connection_state") == "backend_ready"
    assert local[0].get("capability_summary", {}).get("readonly", 0) >= 1


def test_orchestration_preflight_creates_job_when_railway_ready(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._resolve_railway_token_canonical",
        lambda: ("token", "test", None),
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks._probe_github_binding",
        lambda **kwargs: {"github_credential_ok": True, "accessible_repos_count": 1, "detail": "ok"},
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.credential_truth.list_services_with_status",
        lambda token: {"ok": True, "services": [{"project_name": "aethos", "service_name": "aethos-api"}], "error": None},
    )
    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan.readiness_check_statuses",
        lambda checks: {"cred": True, "api": True, "inventory": True},
    )
    inventory = type(
        "Inv",
        (),
        {
            "error": None,
            "freshness": "test",
            "evidence": {},
            "projects": [
                type(
                    "P",
                    (),
                    {
                        "id": "p1",
                        "name": "aethos",
                        "environments": [
                            type(
                                "E",
                                (),
                                {
                                    "id": "e1",
                                    "name": "production",
                                    "services": [type("S", (), {"name": "aethos-api"})()],
                                },
                            )()
                        ],
                    },
                )()
            ],
        },
    )()
    monkeypatch.setattr(
        "aethos_core.providers.railway.discovery.safe_discover_railway_inventory",
        lambda: inventory,
    )
    routed = route_provider_deploy_capability_reply(RAILWAY_E2E_PROMPT, session_id="sprint-job")
    assert routed is not None
    _reply, intent, meta = routed
    assert intent == "railway_e2e_orchestration_preflight"
    assert len(job_store.list_all()) == 1
    assert meta.get("mutation_performed") == "false"
