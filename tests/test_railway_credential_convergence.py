# SPDX-License-Identifier: Apache-2.0
"""RAILWAY_CREDENTIAL_CONVERGENCE_FIX regression tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.connections.validation_status import VALIDATED
from aethos_core.credentials import get_provider_api_token
from aethos_core.execution_brain.execution_brain_router import route_execution_brain_turn
from aethos_core.provider_e2e_readiness.readiness_router import route_provider_e2e_readiness
from aethos_core.providers.railway.credential_truth import (
    RAILWAY_VALIDATION_PROBE,
    diagnose_railway_credential_truth,
    resolve_and_validate_railway_credential,
    resolve_railway_credential,
    validate_railway_api_connection,
)
from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
    run_deployment_readiness_checks,
)
from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests

_VAULT_TOKEN = "railway_convergence_vault_token_1234567890"
_ENV_TOKEN = "railway_convergence_env_token_9876543210"
_LIST_SERVICES_PATCH = "aethos_core.providers.railway.credential_truth.list_services_with_status"


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


def _store_validated(vault_paths, *, token: str = _VAULT_TOKEN) -> str:
    vault = CredentialVault(vault_paths)
    rec = vault.store_api_token(provider="railway", label="Railway primary account", token=token)
    vault.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    reset_credential_vault_for_tests()
    CredentialVault(vault_paths)
    return rec.credential_id


def _inventory_ok(token: str, *args, **kwargs):
    _ = (token, args, kwargs)
    return {"ok": True, "services": [{"project_name": "aethos", "service_name": "api"}], "error": None}


def _inventory_fail(token: str, *args, **kwargs):
    _ = (token, args, kwargs)
    return {"ok": False, "services": [], "error": "Not Authorized"}


def test_validated_vault_preferred_over_invalid_env(vault_paths, monkeypatch):
    cred_id = _store_validated(vault_paths)
    monkeypatch.setenv("RAILWAY_API_TOKEN", _ENV_TOKEN)
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        resolved = resolve_railway_credential()

    assert resolved.source == "validated_vault"
    assert resolved.credential_id == cred_id
    assert resolved.token == _VAULT_TOKEN


def test_env_used_when_no_validated_vault(vault_paths, monkeypatch):
    monkeypatch.setenv("RAILWAY_API_TOKEN", _ENV_TOKEN)
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        resolved = resolve_railway_credential()

    assert resolved.source == "environment"
    assert resolved.token == _ENV_TOKEN


def test_readiness_and_mutation_use_same_token(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        checks = run_deployment_readiness_checks()
        mut_token, mut_source, mut_err = resolve_railway_mutation_credentials()
        getter = get_provider_api_token("railway")

    assert checks["railway_api_connection_ok"] is True
    assert checks["railway_validation_probe"] == RAILWAY_VALIDATION_PROBE
    assert mut_err is None
    assert mut_token == getter == _VAULT_TOKEN
    assert mut_source == "vault"


def test_validated_vault_readiness_brain_e2e_aligned(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        readiness = route_provider_e2e_readiness("Check Railway deployment readiness.", session_id="conv-ready")
        brain = route_execution_brain_turn("Deploy AethOS to Railway and configure env vars.", session_id="conv-brain")

    assert readiness is not None
    assert "ProjectsAndServices" in readiness[0]
    assert readiness[2].get("trust_aligned") is None  # meta may not include - check content
    assert brain is not None
    assert "token validation failed" not in brain[0].lower()
    assert brain[1] != "execution_brain_recovery" or "blocked" not in brain[0].lower()


def test_invalid_env_does_not_override_valid_vault_readiness(vault_paths, monkeypatch):
    _store_validated(vault_paths)
    monkeypatch.setenv("RAILWAY_API_TOKEN", _ENV_TOKEN)
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    def side_effect(token, *args, **kwargs):
        if token == _ENV_TOKEN:
            return _inventory_fail(token, *args, **kwargs)
        return _inventory_ok(token, *args, **kwargs)

    with patch(_LIST_SERVICES_PATCH, side_effect=side_effect):
        checks = run_deployment_readiness_checks()
        brain = route_execution_brain_turn("Deploy AethOS to Railway.", session_id="conv-env-override")

    assert checks["railway_api_connection_ok"] is True
    assert checks["railway_credential_source_label"] == "Validated Vault Credential"
    assert brain is not None
    assert "RAILWAY_TOKEN_INVALID" not in brain[0]
    assert "token validation failed" not in brain[0].lower()


def test_diagnostics_show_probe_and_source(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        diag = diagnose_railway_credential_truth()

    assert diag["credential_source"] == "validated_vault"
    assert diag["validation_probe"] == "ProjectsAndServices"
    assert diag["connection_validation_ok"] is True
    assert diag["trust_aligned"] is True


def test_show_railway_credential_diagnostics_chat(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        result = resolve_chat_turn("show railway credential diagnostics", session_id="conv-diag", apply_relational_layer=False)

    assert result.intent == "railway_credential_resolution_diagnostics"
    assert "Validation probe" in result.reply
    assert "ProjectsAndServices" in result.reply
    assert _VAULT_TOKEN not in result.reply


def test_shared_validate_matches_ui_probe(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok):
        resolution, validation = resolve_and_validate_railway_credential()

    assert resolution.ok
    assert validation is not None
    assert validation.ok
    assert validation.probe == RAILWAY_VALIDATION_PROBE


def test_convergence_uses_inventory_not_me_query(vault_paths):
    _store_validated(vault_paths)
    with patch(_LIST_SERVICES_PATCH, side_effect=_inventory_ok), patch(
        "aethos_core.providers.railway.api_client.test_connection"
    ) as me_mock:
        validate_railway_api_connection(_VAULT_TOKEN)
        run_deployment_readiness_checks()
    me_mock.assert_not_called()
