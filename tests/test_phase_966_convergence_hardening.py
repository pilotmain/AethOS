# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.connections.credential_validation import validate_provider_credential
from aethos_core.connections.validation_status import VALIDATED
from aethos_core.operations.intents import infer_operation_preflight_intent
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


def test_railway_validation_uses_readonly_inventory_path(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(
        provider="railway",
        label="Primary",
        token="railway_inventory_validate_1234567890",
    )
    with patch(
        "aethos_core.providers.railway.credential_truth.list_services_with_status",
        return_value={"ok": True, "services": [{"name": "svc-a", "project_name": "p1"}]},
    ) as inventory_mock:
        result = validate_provider_credential(provider="railway", credential_id=rec.credential_id)
    assert result["ok"] is True
    assert result["validation_status"] == VALIDATED
    inventory_mock.assert_called_once()
    assert result["diagnostics"]["readonly_inventory_ok"] is True
    assert result["diagnostics"]["graphql_operation"] == "ProjectsAndServices"


def test_railway_me_query_not_used_for_validation(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="railway", label="Primary", token="railway_no_me_query_1234567890")
    with patch(
        "aethos_core.providers.railway.credential_truth.list_services_with_status",
        return_value={"ok": True, "services": [{"name": "svc", "project_name": "p"}]},
    ), patch("aethos_core.providers.railway.api_client.test_connection") as me_mock:
        validate_provider_credential(provider="railway", credential_id=rec.credential_id)
    me_mock.assert_not_called()


def test_partial_railway_provider_typo_routes_restart(vault_paths):
    out = infer_operation_preflight_intent("restart speakglobal-ai on Railwa")
    assert out is not None
    _title, _job_type, params = out
    assert params["provider"] == "railway"
    assert params["operation_type"] == "restart"


def test_github_discovery_uses_readonly_substrate(vault_paths):
    v1 = CredentialVault(vault_paths)
    v1.store_api_token(provider="github", label="gh", token="ghp_discovery_substrate_1234567890")
    reset_credential_vault_for_tests()

    artifact = {
        "ok": True,
        "repository": "pilotmain/AethOS",
        "runs": [
            {
                "id": 99,
                "workflow_id": 1,
                "name": "CI",
                "status": "completed",
                "conclusion": "failure",
                "run_number": 12,
            }
        ],
        "discovery_source": "readonly_execution_artifact",
        "source_job_id": "job-test",
    }
    with patch(
        "aethos_core.providers.github.shared.readonly_workflow_artifact.find_recent_readonly_workflow_runs_artifact",
        return_value=artifact,
    ), patch(
        "aethos_core.operations.orchestration.target_resolution.canonical_resolver.canonical_resolve_target",
        return_value=type("R", (), {"status": "resolved", "target_name": "pilotmain/AethOS"})(),
    ), patch(
        "aethos_core.providers.github.mutations.workflow_rerun_preflight.discover_workflow_rerun_from_readonly_substrate",
        return_value={
            "ok": True,
            "repository": "pilotmain/AethOS",
            "workflow_name": "CI",
            "source_run_number": 12,
            "workflow_resolution_debug": {"discovery_source": "readonly_execution_artifact", "workflow_candidates_found": 1},
        },
    ) as discover_mock:
        out = _discover_github_workflow_for_mutation(
            target_name="pilotmain/AethOS",
            user_request="rerun latest workflow for AethOS",
            target_hints=["AethOS"],
        )
    discover_mock.assert_called_once()
    assert discover_mock.call_args.kwargs["readonly_artifact"] == artifact
    assert out["ok"] is True


def test_reload_credential_runtime_refreshes_vault(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="vercel", label="vc", token="vercel_reload_runtime_1234567890")
    reset_credential_vault_for_tests()
    from aethos_core.connections.credential_hydration import reload_credential_runtime

    with patch(
        "aethos_core.connections.credential_validation._validate_vercel_runtime",
        return_value={"ok": True, "validation_status": VALIDATED, "diagnostics": {}},
    ):
        reload_credential_runtime(validate=True)
    loaded = get_credential_vault().get(rec.credential_id)
    assert loaded is not None
    assert loaded.validation_status == VALIDATED
