# SPDX-License-Identifier: Apache-2.0
"""Phase 9.6.6 — durable credential persistence + provider auth validation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.connections.credential_hydration import hydrate_credentials_at_startup
from aethos_core.connections.credential_validation import validate_provider_credential
from aethos_core.connections.validation_status import CONFIGURED, MISSING, VALIDATED
from aethos_core.operations.mutations.preflight import _discover_github_workflow_for_mutation
from aethos_core.security.credential_vault import CredentialVault, get_credential_vault, reset_credential_vault_for_tests


@pytest.fixture
def vault_paths(tmp_path, monkeypatch):
    cred_dir = tmp_path / "credentials"
    monkeypatch.setenv("CREDENTIALS_DIR", str(cred_dir))
    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield cred_dir
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def test_credential_record_persists_validation_fields(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(
        provider="github",
        label="Primary",
        token="ghp_test_persist_validation_1234567890",  # gitleaks:allow - synthetic fixture
    )
    v1.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    reset_credential_vault_for_tests()
    v2 = get_credential_vault()
    loaded = v2.get(rec.credential_id)
    assert loaded is not None
    assert loaded.validation_status == VALIDATED
    assert loaded.last_validated_at is not None
    assert loaded.masked_identifier
    secret = v2.retrieve_secret(rec.credential_id)
    assert secret is not None
    assert secret["token"] == "ghp_test_persist_validation_1234567890"  # gitleaks:allow


def test_startup_hydration_loads_all_providers(vault_paths):
    v1 = CredentialVault(vault_paths)
    v1.store_api_token(
        provider="github",
        label="gh",
        token="ghp_hydrate_test_123456789012",  # gitleaks:allow - synthetic fixture
    )
    v1.store_api_token(provider="railway", label="rw", token="railway_hydrate_test_1234567890")
    v1.store_api_token(provider="vercel", label="vc", token="vercel_hydrate_test_1234567890")  # gitleaks:allow - fixture
    reset_credential_vault_for_tests()

    with patch(
        "aethos_core.connections.credential_validation._validate_via_runtime",
        return_value={"ok": True, "validation_status": VALIDATED, "diagnostics": {}},
    ):
        report = hydrate_credentials_at_startup(validate=True)

    assert report["credential_count"] == 3
    assert report["validated_count"] == 3
    assert report["providers"]["github"]["status"] == VALIDATED


def test_rotate_api_token_without_restart(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="railway", label="Primary", token="railway_old_token_1234567890")
    v1.rotate_api_token(rec.credential_id, token="railway_new_token_1234567890")
    secret = v1.retrieve_secret(rec.credential_id)
    assert secret["token"] == "railway_new_token_1234567890"
    updated = v1.get(rec.credential_id)
    assert updated.validation_status == CONFIGURED


def test_github_discovery_includes_auth_diagnostics(vault_paths):
    v1 = CredentialVault(vault_paths)
    v1.store_api_token(provider="github", label="gh", token="ghp_discovery_diag_1234567890")
    reset_credential_vault_for_tests()

    with patch(
        "aethos_core.providers.github.mutations.workflow_rerun_preflight.discover_workflow_rerun_from_readonly_substrate",
        return_value={
            "ok": False,
            "discovery_failure_reason": "no_workflow_runs",
            "workflow_resolution_debug": {
                "auth_state": "validated",
                "workflow_scope_present": True,
                "repository_access": True,
                "api_status": 200,
                "workflow_candidates_found": 0,
                "rerunnable_candidates_found": 0,
                "discovery_failure_reason": "no_workflow_runs",
            },
            "discovery_diagnostics": {
                "auth_state": "validated",
                "workflow_scope_present": True,
                "repository_access": True,
                "api_status": 200,
            },
        },
    ), patch(
        "aethos_core.providers.github.shared.readonly_workflow_artifact.find_recent_readonly_workflow_runs_artifact",
        return_value=None,
    ):
        out = _discover_github_workflow_for_mutation(
            target_name="org/AethOS",
            user_request="rerun for org/AethOS",
        )

    diag = out.get("discovery_diagnostics") or out.get("workflow_resolution_debug") or {}
    assert "auth_state" in diag
    assert "workflow_scope_present" in diag
    assert "repository_access" in diag
    assert "api_status" in diag


def test_validate_missing_secret_marks_secret_missing(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(
        provider="github",
        label="gh",
        token="ghp_missing_secret_1234567890",  # gitleaks:allow - synthetic fixture
    )
    v1._delete_secret(rec.credential_id)
    result = validate_provider_credential(provider="github", credential_id=rec.credential_id)
    assert result["ok"] is False
    assert result["validation_status"] == "reconnect_required"
    assert result["failure_class"] == "encrypted_secret_missing"


def test_credential_center_reports_missing_provider(vault_paths):
    from aethos_core.connections.credential_hydration import build_credential_center_payload

    reset_credential_vault_for_tests()
    payload = build_credential_center_payload()
    github = next(p for p in payload["providers"] if p["provider"] == "github")
    assert github["status"] == MISSING
