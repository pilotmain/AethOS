# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8B.3 — durable credential vault recovery + storage consistency."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.connections.credential_hydration import build_credential_center_payload, hydrate_credentials_at_startup
from aethos_core.connections.credential_repair import repair_metadata_only_credentials, repair_provider_credential
from aethos_core.connections.credential_runtime_gate import check_provider_credential_gate
from aethos_core.connections.credential_state import resolve_credential_state
from aethos_core.connections.credential_validation import validate_provider_credential
from aethos_core.connections.validation_status import RECONNECT_REQUIRED, VALIDATED
from aethos_core.operations.mutations.preflight import _mutation_provider_auth_block
from aethos_core.operations.orchestration.provider_runtime import get_provider_api_token, resolve_execution_auth
from aethos_core.security.credential_paths import credential_index_path, credential_secret_path
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


def test_valid_token_survives_restart(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="railway", label="Primary", token="railway_persist_restart_1234567890")
    v1.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    secret_path = credential_secret_path(rec.credential_id)
    assert secret_path.is_file()

    reset_credential_vault_for_tests()
    v2 = get_credential_vault()
    loaded = v2.get(rec.credential_id)
    assert loaded is not None
    state = resolve_credential_state(rec.credential_id)
    assert state["decryptable"] is True
    assert state["auth_source"] == "encrypted_vault"
    secret = v2.retrieve_secret(rec.credential_id)
    assert secret["token"] == "railway_persist_restart_1234567890"


def test_save_and_load_paths_match(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="github", label="gh", token="ghp_path_consistency_1234567890")
    save_path = credential_secret_path(rec.credential_id)
    reset_credential_vault_for_tests()
    load_path = credential_secret_path(rec.credential_id)
    assert save_path.resolve() == load_path.resolve()
    assert load_path.is_file()


def test_metadata_only_detection_after_enc_deleted(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="railway", label="rw", token="railway_metadata_only_1234567890")
    v1.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    v1._delete_secret(rec.credential_id)
    reset_credential_vault_for_tests()

    with patch(
        "aethos_core.connections.credential_validation._validate_via_runtime",
        return_value={"ok": True, "validation_status": VALIDATED, "diagnostics": {}},
    ):
        report = hydrate_credentials_at_startup(validate=False)

    provider_row = report["providers"]["railway"]
    assert provider_row["metadata_found"] is True
    assert provider_row["encrypted_secret_found"] is False
    assert provider_row["decryptable"] is False
    assert provider_row["hydrated"] is False
    assert provider_row["credential_state"] == RECONNECT_REQUIRED

    center = build_credential_center_payload()
    railway = next(p for p in center["providers"] if p["provider"] == "railway")
    assert railway["credential_state"] == RECONNECT_REQUIRED
    assert railway["auth_source"] == "metadata_only"
    assert railway["actions_allowed"]["revalidate"] is False


def test_repair_metadata_only_marks_reconnect_required(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="vercel", label="vc", token="vercel_repair_scan_123456789012")
    v1._delete_secret(rec.credential_id)
    reset_credential_vault_for_tests()

    repaired = repair_metadata_only_credentials()
    assert any(row["credential_id"] == rec.credential_id for row in repaired)
    state = resolve_credential_state(rec.credential_id)
    assert state["credential_state"] == RECONNECT_REQUIRED


def test_reconnect_repair_recreates_secret(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="github", label="gh", token="ghp_old_repair_token_1234567890")
    v1._delete_secret(rec.credential_id)
    reset_credential_vault_for_tests()

    with patch(
        "aethos_core.connections.credential_validation._validate_via_runtime",
        return_value={"ok": True, "validation_status": VALIDATED, "diagnostics": {}},
    ):
        result = repair_provider_credential(
            provider="github",
            token="ghp_new_repair_token_1234567890",
        )

    assert result["decryptable"] is True
    assert result["auth_source"] == "encrypted_vault"
    assert credential_secret_path(result["credential_id"]).is_file()
    secret = get_credential_vault().retrieve_secret(result["credential_id"])
    assert secret["token"] == "ghp_new_repair_token_1234567890"


def test_runtime_gating_blocks_metadata_only(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="railway", label="rw", token="railway_runtime_gate_1234567890")
    v1.mark_validation_result(rec.credential_id, status=VALIDATED, ok=True)
    v1._delete_secret(rec.credential_id)
    reset_credential_vault_for_tests()

    gate = check_provider_credential_gate("railway", require_validated=True)
    assert gate["ok"] is False
    assert "reconnect required" in gate["detail"].lower()

    auth = resolve_execution_auth(provider="railway", operation_type="read_projects", params={})
    token = get_provider_api_token(provider="railway", auth=auth)
    assert token is None

    preflight = _mutation_provider_auth_block(provider="railway", operation_type="restart_service")
    assert preflight == "needs_credential_repair"


def test_validate_missing_secret_marks_reconnect_required(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(
        provider="github",
        label="gh",
        token="ghp_missing_secret_1234567890",  # gitleaks:allow - synthetic fixture
    )
    v1._delete_secret(rec.credential_id)
    result = validate_provider_credential(provider="github", credential_id=rec.credential_id)
    assert result["ok"] is False
    assert result["validation_status"] == RECONNECT_REQUIRED
    assert result["failure_class"] == "encrypted_secret_missing"


def test_persistence_validation_requires_enc_file(vault_paths, monkeypatch):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="github", label="gh", token="ghp_persist_check_123456789012")
    enc = credential_secret_path(rec.credential_id)
    assert enc.is_file()

    def _fail_write(*_args, **_kwargs):
        raise OSError("simulated write failure")

    monkeypatch.setattr(enc.__class__, "write_bytes", _fail_write)
    with pytest.raises(Exception):
        v1.rotate_api_token(rec.credential_id, token="ghp_persist_check_rotated_1234567890")


def test_credential_index_under_canonical_root(vault_paths):
    v1 = CredentialVault(vault_paths)
    v1.store_api_token(provider="github", label="gh", token="ghp_index_root_12345678901234")
    assert credential_index_path().is_file()
    assert credential_index_path().parent.resolve() == vault_paths.resolve()
