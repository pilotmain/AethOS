# SPDX-License-Identifier: Apache-2.0
"""Phase 9.8B.1 stabilization tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.browser.runtime.browser_artifacts import store_artifact
from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.security.credential_vault import CredentialVault


@pytest.fixture
def vault_paths(tmp_path, monkeypatch):
    cred_dir = tmp_path / "credentials"
    monkeypatch.setenv("CREDENTIALS_DIR", str(cred_dir))
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield cred_dir
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def browser_artifacts_env(monkeypatch, tmp_path):
    root = tmp_path / "browser_artifacts"
    monkeypatch.setenv("BROWSER_ARTIFACTS_DIR", str(root))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield root
    get_settings.cache_clear()


def test_credential_vault_reads_encrypted_file_when_keyring_empty(vault_paths):
    v1 = CredentialVault(vault_paths)
    rec = v1.store_api_token(provider="railway", label="rw", token="7063testtoken1234567890")
    enc = vault_paths / "secrets" / f"{rec.credential_id}.enc"
    assert enc.is_file()

    with patch("aethos_core.security.credential_vault._keyring_available", return_value=True):
        import sys
        from unittest.mock import MagicMock

        mock_kr = MagicMock()
        mock_kr.get_password.return_value = None
        with patch.dict(sys.modules, {"keyring": mock_kr}):
            v2 = CredentialVault(vault_paths)
            secret = v2.retrieve_secret(rec.credential_id)
    assert secret is not None
    assert secret.get("token") == "7063testtoken1234567890"
    diag = v2.inspect_secret_storage(rec.credential_id)
    assert diag["decryptable"] is True
    assert diag["has_encrypted_secret"] is True


def test_browser_artifact_file_endpoint_returns_image(browser_artifacts_env):
    meta = store_artifact(
        capture_type="screenshot",
        source_url="https://useinvoicepilot.com",
        session_id="test",
        headless=True,
        approved=True,
        risk_tier="T1",
        payload={},
        binary=b"\x89PNG\r\n\x1a\nfake",
        artifact_type="browser_screenshot",
    )
    assert meta["file_exists"] is True
    assert meta["file_size_bytes"] > 0

    from aethos_core.api.main import app

    client = TestClient(app)
    res = client.get(f"/api/v1/browser/artifacts/{meta['artifact_id']}/file")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/png")


def test_artifact_file_api_path_helper():
    from aethos_core.browser.runtime.browser_artifacts import artifact_file_api_path

    assert artifact_file_api_path("bart-test") == "/api/v1/browser/artifacts/bart-test/file"


def test_deployment_evidence_prefers_browser_lane_over_vercel_preflight():
    from aethos_core.browser.runtime.browser_evidence_intents import infer_browser_evidence_job
    from aethos_core.chat.handlers import resolve_handler

    msg = "capture deployment evidence for speakglobal-ai"
    assert infer_browser_evidence_job(msg) is not None
    out = resolve_handler(msg, session_id="web-test")
    assert out is not None
    assert out[1] == "browser_evidence_job_created"


def test_inventory_routes_speakglobal_to_railway_preflight_when_not_browser_capture():
    from aethos_core.runtime.authority import authority
    from aethos_core.runtime.jobs import job_store

    job = authority.create_job(
        title="Railway inventory",
        job_type="railway_services_inventory",
        params={
            "railway_inventory": {
                "items": [
                    {"name": "speakglobal-ai", "service_name": "speakglobal-ai", "url": "https://speakglobal.ai"},
                ],
            },
        },
        source="test",
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result="ok",
        summary="ok",
        preview="ok",
        provider="railway_api",
        model="graphql",
        used_llm=False,
        fallback=False,
    )

    out = infer_operation_preflight_intent("show deployments for speakglobal-ai")
    assert out is not None
    assert out[2]["provider"] == "railway"


def test_provider_inference_resolves_railway_target():
    from aethos_core.operations.orchestration.provider_inference import infer_provider_for_hints
    from aethos_core.runtime.authority import authority
    from aethos_core.runtime.jobs import job_store

    job = authority.create_job(
        title="Railway inventory",
        job_type="railway_services_inventory",
        params={
            "railway_inventory": {
                "items": [{"name": "speakglobal-ai", "url": "https://speakglobal.ai"}],
            },
        },
        source="test",
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result="ok",
        summary="ok",
        preview="ok",
        provider="railway_api",
        model="graphql",
        used_llm=False,
        fallback=False,
    )

    inferred = infer_provider_for_hints(["speakglobal-ai"])
    assert inferred["status"] == "resolved"
    assert inferred["provider"] == "railway"


def test_mutation_preflight_blocks_railway_without_credential(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.operations.mutations.preflight import run_mutation_preflight

    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value="needs_credential",
    ):
        outcome = run_mutation_preflight(
            job_type="mutation_preflight",
            params={
                "user_request": "restart speakglobal-ai on Railway",
                "provider": "railway",
                "operation_type": "restart",
                "target_name": "speakglobal-ai",
            },
        )
    assert outcome.preflight_status == "needs_credential"
    assert outcome.discovery_failure_reason == "provider_auth_failure"
    get_settings.cache_clear()
