# SPDX-License-Identifier: Apache-2.0
"""RAILWAY_INVENTORY_DISCOVERY_FIX regression tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.connections.validation_status import VALIDATED
from aethos_core.execution_brain.execution_brain_router import route_execution_brain_turn
from aethos_core.provider_e2e_readiness.readiness_router import route_provider_e2e_readiness
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
    run_deployment_readiness_checks,
)
from aethos_core.providers.railway.discovery import discover_railway_inventory, safe_discover_railway_inventory
from aethos_core.providers.railway.inventory.railway_inventory_discovery import (
    parse_projects_environments_services_payload,
)
from aethos_core.providers.railway.inventory.railway_projects_chat import format_railway_projects_inventory_reply
from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests

_SECRET = "railway_inventory_secret_token_1234567890"
_LIST_SERVICES_PATCH = "aethos_core.providers.railway.credential_truth.list_services_with_status"


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
def vault_paths(tmp_path, monkeypatch):
    cred_dir = tmp_path / "credentials"
    monkeypatch.setenv("CREDENTIALS_DIR", str(cred_dir))
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    monkeypatch.setattr(settings, "railway_api_token", "")
    yield cred_dir
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def _store_validated(vault_paths) -> None:
    vault = CredentialVault(vault_paths)
    rec = vault.store_api_token(provider="railway", label="Railway primary", token=_SECRET)
    vault.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    reset_credential_vault_for_tests()
    CredentialVault(vault_paths)


def _graphql_ok(*args, **kwargs):
    return {
        "ok": True,
        "data": {
            "projects": {
                "edges": [
                    {
                        "node": {
                            "id": "proj-a",
                            "name": "aethos",
                            "environments": {
                                "edges": [{"node": {"id": "env-prod", "name": "production"}}]
                            },
                            "services": {
                                "edges": [
                                    {"node": {"id": "svc-api", "name": "api"}},
                                    {"node": {"id": "svc-worker", "name": "worker"}},
                                ]
                            },
                        }
                    }
                ]
            }
        },
    }


def _inventory_ok(token, *args, **kwargs):
    _ = (token, args, kwargs)
    return {"ok": True, "services": [{"project_name": "aethos", "service_name": "api"}], "error": None}


def test_parse_handles_edges_nodes_and_empty_projects():
    parsed = parse_projects_environments_services_payload({"projects": {"edges": []}})
    assert parsed.ok is True
    assert parsed.project_count == 0
    assert parsed.service_count == 0

    parsed = parse_projects_environments_services_payload(
        {
            "projects": {
                "edges": [
                    {
                        "node": {
                            "id": "p1",
                            "name": "demo",
                            "environments": None,
                            "services": {"edges": [{"node": {"id": "s1", "name": "api"}}]},
                        }
                    }
                ]
            }
        }
    )
    assert parsed.project_count == 1
    assert parsed.service_count == 1
    assert parsed.projects[0]["environments"][0]["name"] == "production"


def test_show_railway_projects_success(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.inventory.railway_inventory_discovery.graphql_query",
        side_effect=_graphql_ok,
    ):
        kernel = route_operational_conversation_kernel_turn("show Railway projects", session_id="inv-ok")
        chat = resolve_chat_turn("show Railway projects", session_id="inv-ok", apply_relational_layer=False)

    assert kernel is not None
    assert "aethos" in kernel.reply
    assert "api" in kernel.reply or "projects" in kernel.reply.lower()
    assert _SECRET not in kernel.reply
    assert "internal error" not in kernel.reply.lower()
    assert "cogerr" not in kernel.reply.lower()
    assert chat.intent.startswith("operational_kernel")
    assert "cogerr" not in (chat.reply or "").lower()


def test_show_railway_projects_graphql_error(vault_paths):
    _store_validated(vault_paths)

    def graphql_fail(token, query, variables=None):
        _ = (token, query, variables)
        return {"ok": False, "errors": [{"message": "Not Authorized"}]}

    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.inventory.railway_inventory_discovery.graphql_query",
        side_effect=graphql_fail,
    ):
        kernel = route_operational_conversation_kernel_turn("show Railway projects", session_id="inv-graphql-fail")
        chat = resolve_chat_turn("show Railway projects", session_id="inv-graphql-fail", apply_relational_layer=False)

    assert kernel is not None
    assert "inventory" in kernel.reply.lower()
    assert (
        "not authorized" in kernel.reply.lower()
        or "not accessible" in kernel.reply.lower()
        or "isn't available" in kernel.reply.lower()
        or "unavailable" in kernel.reply.lower()
        or "discovery failed" in kernel.reply.lower()
    )
    assert _SECRET not in kernel.reply
    assert "cogerr" not in (chat.reply or "").lower()
    assert "internal error" not in (chat.reply or "").lower()


def test_show_railway_projects_malformed_response(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.inventory.railway_inventory_discovery.graphql_query",
        return_value={"ok": True, "data": "unexpected"},
    ):
        inventory = safe_discover_railway_inventory()

    assert inventory.projects == []
    assert inventory.error
    assert "unexpected" in inventory.error.lower() or inventory.freshness == "failed"


def test_show_railway_projects_empty_projects(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.inventory.railway_inventory_discovery.graphql_query",
        return_value={"ok": True, "data": {"projects": {"edges": []}}},
    ):
        kernel = route_operational_conversation_kernel_turn("show Railway projects", session_id="inv-empty")

    assert kernel is not None
    assert "Projects" in kernel.reply or "projects" in kernel.reply.lower()
    assert "cogerr" not in kernel.reply.lower()


def test_readiness_inventory_failure_structured_blocker(vault_paths):
    _store_validated(vault_paths)

    def graphql_fail(token, query, variables=None):
        _ = (token, query, variables)
        return {"ok": False, "errors": [{"message": "permission denied"}]}

    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.inventory.railway_inventory_discovery.graphql_query",
        side_effect=graphql_fail,
    ):
        checks = run_deployment_readiness_checks(user_text="Deploy AethOS to Railway with env vars and verify it")
        readiness = route_provider_e2e_readiness(
            "Check Railway deployment readiness.",
            session_id="inv-readiness",
        )
        kernel = route_operational_conversation_kernel_turn(
            "Deploy AethOS to Railway with env vars and verify it",
            session_id="inv-brain",
        )

    assert checks["railway_api_connection_ok"] is True
    assert checks["inventory"]["ok"] is False
    assert checks["inventory"]["inventory_probe_status"] == "fail"
    assert readiness is not None
    assert "RAILWAY_INVENTORY_UNAVAILABLE" in readiness[0] or "discovery failed" in readiness[0].lower()
    assert kernel is not None
    assert "cogerr" not in kernel.reply.lower()
    assert "internal error" not in kernel.reply.lower()


def test_discovery_no_nameerror_with_services(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.inventory.railway_inventory_discovery.graphql_query",
        side_effect=_graphql_ok,
    ):
        inventory = discover_railway_inventory()

    assert len(inventory.projects) == 1
    assert inventory.projects[0].name == "aethos"
    assert len(inventory.projects[0].environments[0].services) == 2


def test_safe_discover_never_raises(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.discovery._discover_via_api",
        side_effect=RuntimeError("boom"),
    ):
        inventory = safe_discover_railway_inventory()

    assert inventory.freshness == "failed"
    assert "boom" in inventory.error
