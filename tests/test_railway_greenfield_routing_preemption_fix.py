# SPDX-License-Identifier: Apache-2.0
"""RAILWAY_GREENFIELD_ROUTING_PREEMPTION_FIX regression tests."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from aethos_core.chat.cognition_exception_boundary import compose_cognition_crash_fallback, CognitionBoundaryContext
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.connections.validation_status import VALIDATED
from aethos_core.execution_brain.execution_brain_router import route_execution_brain_turn
from aethos_core.provider.completion import ProviderResult
from aethos_core.provider_e2e_execution.railway_e2e_execution import route_railway_e2e_execution
from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
    is_railway_greenfield_deployment_intent,
)
from aethos_core.providers.railway.greenfield_deployment.greenfield_router import (
    route_railway_greenfield_deployment_flow,
)
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests

_SECRET = "railway_greenfield_secret_token_1234567890"
_LIST_SERVICES_PATCH = "aethos_core.providers.railway.credential_truth.list_services_with_status"

EXACT_USER_PROMPT = (
    "but AethOS is a new project and i want you to check local work space and get its remote git "
    "and create a new project in railway and deploy then set all required env vars and report back"
)

GREENFIELD_PROMPT = (
    "AethOS is a new project. Check local workspace, get its remote git, "
    "create a new Railway project, deploy, set required env vars, and report back."
)


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


@pytest.fixture
def local_repo(tmp_path):
    repo = tmp_path / "AethOS"
    repo.mkdir()
    (repo / "pyproject.toml").write_text("[project]\nname = 'aethos'\n", encoding="utf-8")
    (repo / ".env.example").write_text("ANTHROPIC_API_KEY=\nDATABASE_URL=\nPORT=8010\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "ops@example.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "AethOS Test"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:pilotmain/AethOS.git"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


def _store_validated(vault_paths) -> None:
    vault = CredentialVault(vault_paths)
    rec = vault.store_api_token(provider="railway", label="Railway primary", token=_SECRET)
    vault.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    reset_credential_vault_for_tests()
    CredentialVault(vault_paths)


def _inventory_ok(token, *args, **kwargs):
    _ = (token, args, kwargs)
    return {"ok": True, "services": [], "error": None}


def _patch_workspace(monkeypatch, local_repo):
    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.local_workspace_source.resolve_configured_workspace_root",
        lambda: local_repo,
    )


def test_exact_user_prompt_matches_greenfield_intent():
    assert is_railway_greenfield_deployment_intent(EXACT_USER_PROMPT)


def test_exact_prompt_routes_to_greenfield_flow(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    _patch_workspace(monkeypatch, local_repo)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        chat = resolve_chat_turn(EXACT_USER_PROMPT, session_id="gf-exact", apply_relational_layer=False)

    assert chat.meta.get("route_id") == "railway_greenfield_deployment_flow"
    assert chat.meta.get("route_precedence") == "greenfield_before_operational_recall"
    assert chat.meta.get("mutation_performed") == "false"
    assert "recalling the" not in chat.reply.lower()
    assert "cogerr" not in chat.reply.lower()
    assert "TARGET_SERVICE_MISSING" not in chat.reply


def test_exact_prompt_does_not_call_operational_recall(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    _patch_workspace(monkeypatch, local_repo)
    operational = MagicMock(return_value=None)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.chat.cognition_exception_boundary.safe_resolve_operational_turn",
        operational,
    ):
        resolve_chat_turn(EXACT_USER_PROMPT, session_id="gf-no-op-recall", apply_relational_layer=False)

    operational.assert_not_called()


def test_exact_prompt_does_not_call_existing_service_resolver(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    _patch_workspace(monkeypatch, local_repo)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        assert route_railway_e2e_execution(EXACT_USER_PROMPT, session_id="gf-no-e2e") is None
        assert route_execution_brain_turn(EXACT_USER_PROMPT, session_id="gf-no-brain") is None


def test_exact_prompt_does_not_call_llm_fallback(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    _patch_workspace(monkeypatch, local_repo)
    llm = MagicMock(
        return_value=ProviderResult(text="generic llm answer", used_llm=True, provider="test", model="test")
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.provider.completion.complete_chat",
        llm,
    ):
        chat = resolve_chat_turn(EXACT_USER_PROMPT, session_id="gf-no-llm", apply_relational_layer=False)

    llm.assert_not_called()
    assert chat.used_llm is False


def test_exact_prompt_returns_blocker_or_preflight(vault_paths, local_repo, monkeypatch):
    _store_validated(vault_paths)
    _patch_workspace(monkeypatch, local_repo)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        chat = resolve_chat_turn(EXACT_USER_PROMPT, session_id="gf-outcome", apply_relational_layer=False)

    allowed_intents = {
        "railway_greenfield_deployment_preflight",
        "railway_greenfield_deployment_blocked",
    }
    assert chat.intent in allowed_intents
    if chat.intent == "railway_greenfield_deployment_blocked":
        assert chat.meta.get("blocker_code") in {
            "LOCAL_WORKSPACE_NOT_CONFIGURED",
            "GIT_REMOTE_MISSING",
            "RAILWAY_TOKEN_MISSING",
            "RAILWAY_TOKEN_INVALID",
            "RAILWAY_GREENFIELD_FLOW_ERROR",
        }
    else:
        assert chat.meta.get("preflight_created") == "true"


def test_cognition_crash_fallback_prefers_greenfield_over_investigation_recall(
    vault_paths, local_repo, monkeypatch
):
    _store_validated(vault_paths)
    _patch_workspace(monkeypatch, local_repo)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        result = compose_cognition_crash_fallback(
            RuntimeError("simulated crash"),
            CognitionBoundaryContext(text=EXACT_USER_PROMPT, session_id="gf-crash"),
        )

    assert result.meta.get("route_id") == "railway_greenfield_deployment_flow"
    assert "recalling the" not in result.reply.lower()
    assert "cogerr" not in result.reply.lower()


def test_flow_exception_still_routes_greenfield_not_investigation(vault_paths, monkeypatch):
    _store_validated(vault_paths)
    with patch(
        "aethos_core.providers.railway.greenfield_deployment.greenfield_flow._run_railway_greenfield_deployment_flow_impl",
        side_effect=RuntimeError("boom"),
    ):
        routed = route_railway_greenfield_deployment_flow(EXACT_USER_PROMPT, session_id="gf-exception")

    assert routed is not None
    body, intent, meta = routed
    assert intent == "railway_greenfield_deployment_blocked"
    assert meta.get("blocker_code") == "RAILWAY_GREENFIELD_FLOW_ERROR"
    assert "recalling the" not in body.lower()


def test_show_railway_projects_still_routes_inventory(vault_paths, monkeypatch):
    _store_validated(vault_paths)
    inventory = MagicMock(
        return_value=(
            "**Railway projects**",
            "provider_discovery_inventory",
            {"route_id": "railway_projects_inventory"},
        )
    )
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.inventory.railway_projects_chat.route_railway_projects_inventory",
        inventory,
    ):
        chat = resolve_chat_turn("show Railway projects", session_id="inv-still", apply_relational_layer=False)

    inventory.assert_called_once()
    assert chat.intent == "provider_discovery_inventory"


def test_redeploy_existing_service_still_routes_e2e(vault_paths, monkeypatch):
    assert is_railway_greenfield_deployment_intent("redeploy Railway api service") is False
    e2e = MagicMock(return_value=("redeploy path", "provider_e2e_execution", {"route_id": "railway_e2e"}))
    with patch(
        "aethos_core.provider_e2e_execution.provider_e2e_execution_service.route_provider_e2e_execution",
        e2e,
    ) as route_mock:
        chat = resolve_chat_turn("redeploy Railway api service", session_id="redeploy-still", apply_relational_layer=False)

    route_mock.assert_called_once()
    assert chat.intent == "provider_e2e_execution"


def test_recall_investigation_not_greenfield():
    assert is_railway_greenfield_deployment_intent("recall AethOS api investigation") is False


def test_recall_investigation_still_reaches_operational_path(monkeypatch):
    operational = MagicMock(
        return_value=type(
            "R",
            (),
            {
                "reply": "investigation recall",
                "intent": "operational_thread_recall",
                "meta": {},
                "provider_stream": False,
                "used_llm": False,
                "agent_key": "aethos",
                "terminal": True,
                "provider": None,
                "model": None,
            },
        )()
    )
    with patch(
        "aethos_core.providers.railway.greenfield_deployment.greenfield_intent.is_railway_greenfield_deployment_intent",
        return_value=False,
    ), patch(
        "aethos_core.chat.cognition_exception_boundary.safe_resolve_operational_turn",
        operational,
    ), patch(
        "aethos_core.execution_brain.execution_brain_router.route_execution_brain_turn",
        return_value=None,
    ), patch(
        "aethos_core.provider.completion.complete_chat",
        side_effect=AssertionError("LLM should not run"),
    ):
        chat = resolve_chat_turn(
            "recall AethOS api investigation",
            session_id="recall-still",
            apply_relational_layer=False,
        )

    operational.assert_called_once()
    assert chat.intent == "operational_thread_recall"
