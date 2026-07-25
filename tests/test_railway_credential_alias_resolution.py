# SPDX-License-Identifier: Apache-2.0
"""HOTFIX — Credential Center alias resolution for Railway."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.connections.validation_status import VALIDATED
from aethos_core.credentials import get_provider_api_token
from aethos_core.credentials.provider_alias_resolution import normalize_canonical_provider
from aethos_core.providers.railway.deployment_readiness.railway_credential_diagnostics import (
    diagnose_railway_credential_resolution,
    format_railway_credential_diagnostics_report,
    route_railway_credential_diagnostics,
)
from aethos_core.security.credential_vault import CredentialVault, reset_credential_vault_for_tests

_SECRET = "railway_alias_hotfix_token_1234567890"


@pytest.fixture
def vault_paths(tmp_path, monkeypatch):
    cred_dir = tmp_path / "credentials"
    monkeypatch.setenv("CREDENTIALS_DIR", str(cred_dir))
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
    monkeypatch.setenv("RAILWAY_API_TOKEN", "")
    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    monkeypatch.setattr(settings, "railway_api_token", "")
    monkeypatch.setattr(
        "aethos_core.credentials.provider_alias_resolution.env_token_for_canonical_provider",
        lambda _canonical: None,
    )
    yield cred_dir
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def _store_validated(vault_paths, *, provider: str, label: str) -> None:
    vault = CredentialVault(vault_paths)
    rec = vault.store_api_token(provider=provider, label=label, token=_SECRET)
    vault.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    reset_credential_vault_for_tests()
    reloaded = CredentialVault(vault_paths)
    assert reloaded.get(rec.credential_id) is not None


def test_ui_label_railway_primary_account_resolves_for_railway(vault_paths):
    _store_validated(vault_paths, provider="Railway primary account", label="Railway primary account")

    token = get_provider_api_token("railway")
    assert token == _SECRET


def test_canonical_railway_provider_still_resolves(vault_paths):
    _store_validated(vault_paths, provider="railway", label="Railway primary account")

    token = get_provider_api_token("railway")
    assert token == _SECRET


def test_wrong_provider_does_not_resolve_for_railway(vault_paths):
    _store_validated(vault_paths, provider="github", label="Railway primary account")

    assert get_provider_api_token("railway") is None


def test_no_token_value_printed_in_debug_report(vault_paths):
    _store_validated(vault_paths, provider="Railway primary account", label="Railway primary account")

    diag = diagnose_railway_credential_resolution()
    body = format_railway_credential_diagnostics_report(diag)
    routed = route_railway_credential_diagnostics(
        "debug railway credential resolution",
        session_id="alias-hotfix",
    )

    assert _SECRET not in body
    assert routed is not None
    assert _SECRET not in routed[0]
    assert "Validation probe" in body
    assert "ProjectsAndServices" in body
    assert "Validated Vault Credential" in body
    assert "railway.credential_truth.resolve_railway_credential" in body


def test_normalize_canonical_provider_aliases():
    assert normalize_canonical_provider("Railway") == "railway"
    assert normalize_canonical_provider("Railway primary account") == "railway"
    assert normalize_canonical_provider("RAILWAY_API_TOKEN") == "railway"
    assert normalize_canonical_provider("github") == "github"


@patch("aethos_core.providers.railway.credential_truth.list_services_with_status")
@patch("aethos_core.providers.railway.discovery.discover_railway_inventory")
def test_readiness_passes_with_alias_credential(mock_inventory, mock_inventory_probe, vault_paths):
    _store_validated(vault_paths, provider="Railway primary account", label="Railway primary account")
    mock_inventory_probe.return_value = {
        "ok": True,
        "services": [{"name": "svc", "project_name": "p1"}],
        "error": None,
    }
    mock_inventory.return_value = type(
        "Inv",
        (),
        {"error": None, "freshness": "ok", "projects": []},
    )()

    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        run_deployment_readiness_checks,
    )

    checks = run_deployment_readiness_checks(user_text="run railway deployment readiness")
    assert checks["railway_credential_ok"] is True
    assert _SECRET not in str(checks)
