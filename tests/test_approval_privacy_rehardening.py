# SPDX-License-Identifier: Apache-2.0
"""APPROVAL_PRIVACY_REHARDENING_001 — regression coverage."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(tmp_path))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.api.main import app

    return TestClient(app)


def test_autonomous_execution_disabled_by_default(api_client) -> None:
    r = api_client.get("/api/v1/autonomous-execution/status")
    assert r.status_code == 503


def test_governance_diagnostics_snapshot(api_client) -> None:
    r = api_client.get("/api/v1/governance/diagnostics")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "diagnostics" in body
    assert body["diagnostics"]["autonomous_execution_enabled"] is False


def test_runtime_override_kill_switch(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("AETHOS_WORKSPACE_ROOT", str(tmp_path))
    from aethos_core.governance.governance_override_store import (
        effective_bool_flag,
        save_governance_override,
    )

    assert effective_bool_flag("railway_greenfield_mutation_kill_switch") is False
    save_governance_override(key="railway_greenfield_mutation_kill_switch", value=True)
    assert effective_bool_flag("railway_greenfield_mutation_kill_switch") is True


def test_chat_presentation_bypass_off_by_default(monkeypatch) -> None:
    monkeypatch.setenv("PRESENTATION_BYPASS_CHAT_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.providers.railway.deployment_plan.deployment_plan_presentation import (
        is_railway_deployment_plan_presentation_bypass,
    )

    assert (
        is_railway_deployment_plan_presentation_bypass(
            intent="railway_deployment_plan",
            meta={"presentation_bypass": "true"},
            channel="chat",
        )
        is False
    )


def test_operational_environment_redacts_secrets(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.runtime.operational_environment import resolve_operational_environment

    snap = resolve_operational_environment()
    payload = json.dumps(snap.to_dict())
    assert "Bearer " not in payload


def test_credential_live_validation_can_be_disabled(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CREDENTIAL_LIVE_VALIDATION_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.connections.credential_validation import validate_provider_credential
    from aethos_core.security.credential_vault import get_credential_vault

    vault = get_credential_vault()
    rec = vault.store_api_token(provider="github", label="test", token="ghp_testtoken1234567890")
    with patch("aethos_core.connections.credential_validation._validate_via_runtime") as mocked:
        out = validate_provider_credential(provider="github", credential_id=rec.credential_id)
        mocked.assert_not_called()
    assert out["ok"] is True
    assert "Format-only" in str(out.get("detail") or "")


def test_production_deployment_target_requires_confirmation(api_client) -> None:
    r = api_client.post(
        "/api/v1/deployment-targets/register",
        json={
            "alias": "prod-app",
            "repo": "org/repo",
            "railway_environment": "production",
        },
    )
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "production_binding_confirmation_required"


def test_browser_capture_blocked_without_approval(monkeypatch) -> None:
    monkeypatch.setenv("BROWSER_CAPTURE_APPROVAL_REQUIRED", "true")
    monkeypatch.setenv("AETHOS_LOCAL_ENV_TRUSTED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.provider_e2e_orchestration.env_completion.supabase_browser_phase import (
        collect_supabase_values_from_sources,
    )

    values, trace = collect_supabase_values_from_sources(plan={}, params={"browser_extraction_enabled": True})
    assert trace.get("browser", {}).get("blocked") is True
    assert "browser_extraction" not in trace.get("sources", [])
    assert not values


def test_cloud_readonly_inventory_stub_disabled() -> None:
    from aethos_core.providers.cloud.readonly_inventory import fetch_cloud_readonly_inventory

    out = fetch_cloud_readonly_inventory(provider="cloudflare")
    assert out["ok"] is False
