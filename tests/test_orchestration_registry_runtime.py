# SPDX-License-Identifier: Apache-2.0
"""Phase 9.3M — registry-backed orchestration runtime resolution."""

from unittest.mock import MagicMock

import aethos_core.providers  # noqa: F401 — bootstrap registry
from aethos_core.operations.orchestration.registry_runtime import (
    resolve_provider_execution_auth,
    resolve_readonly_execution_adapter,
)
from aethos_core.providers.base.provider_registry import ProviderRegistry


def test_all_cloud_providers_register_readonly_execution_factory():
    for name in ("vercel", "railway", "github"):
        spec = ProviderRegistry.get(name)
        assert spec is not None
        assert spec.readonly_execution_factory is not None


def test_resolve_readonly_execution_adapter_returns_none_without_credential():
    assert resolve_readonly_execution_adapter("railway", "") is None
    assert resolve_readonly_execution_adapter("unknown", "cred-1") is None


def test_resolve_readonly_execution_adapter_delegates_to_registered_factory(monkeypatch):
    factory = MagicMock(return_value=MagicMock())
    spec = ProviderRegistry.get("github")
    assert spec is not None
    monkeypatch.setattr(spec, "readonly_execution_factory", factory)

    adapter = resolve_readonly_execution_adapter("github", "cred-abc")

    factory.assert_called_once_with("cred-abc")
    assert adapter is factory.return_value


def test_resolve_provider_execution_auth_railway_api_token(monkeypatch):
    from aethos_core.providers.railway.auth import RailwayAuthAdapter

    monkeypatch.setattr(
        RailwayAuthAdapter,
        "resolve_best_auth_method",
        lambda self, *, operation: {
            "method": "api_token",
            "credential_id": "rail-cred",
        },
    )
    auth = resolve_provider_execution_auth("railway")
    assert auth["auth_method"] == "api_token"
    assert auth["credential_id"] == "rail-cred"
    assert auth["browser_used"] is False


def test_resolve_provider_execution_auth_github_api_token(monkeypatch):
    from aethos_core.providers.github.auth import GitHubAuthAdapter

    monkeypatch.setattr(
        GitHubAuthAdapter,
        "resolve_best_auth_method",
        lambda self, *, operation: {
            "method": "api_token",
            "credential_id": "gh-cred",
        },
    )
    auth = resolve_provider_execution_auth("github")
    assert auth["auth_method"] == "api_token"
    assert auth["credential_id"] == "gh-cred"


def test_resolve_provider_execution_auth_vercel_browser(monkeypatch):
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    monkeypatch.setattr(
        VercelAuthAdapter,
        "resolve_best_auth_method",
        lambda self, *, operation: {"method": "browser"},
    )
    auth = resolve_provider_execution_auth("vercel")
    assert auth["auth_method"] == "browser"
    assert auth["browser_used"] is True


def test_resolve_provider_execution_auth_local_returns_empty():
    assert resolve_provider_execution_auth("local") == {}


def test_get_operation_capability_returns_registered_capability():
    cap = ProviderRegistry.get_operation_capability("github", "workflow_runs")
    assert cap is not None
    assert cap.operation == "workflow_runs"
    assert cap.read_only is True


def test_get_operation_capability_unknown_provider_returns_none():
    assert ProviderRegistry.get_operation_capability("unknown", "workflow_runs") is None
    assert ProviderRegistry.get_operation_capability("github", "not_an_operation") is None


def test_registry_preflight_capability_metadata_delegates_to_provider_fn():
    from aethos_core.operations.orchestration.registry_runtime import preflight_capability_metadata

    meta = preflight_capability_metadata("railway", "list_deployments")
    assert "auth_method" in meta
    assert "api_capable" in meta
    assert meta["browser_required"] is False


def test_registry_preflight_capability_metadata_vercel_includes_browser_fields():
    from aethos_core.operations.orchestration.registry_runtime import preflight_capability_metadata

    meta = preflight_capability_metadata("vercel", "list_deployments")
    assert "browser_runtime_required" in meta
    assert "browser_fallback_available" in meta


def test_registry_preflight_capability_metadata_unknown_provider_returns_empty():
    from aethos_core.operations.orchestration.registry_runtime import preflight_capability_metadata

    assert preflight_capability_metadata("unknown", "list_deployments") == {}
