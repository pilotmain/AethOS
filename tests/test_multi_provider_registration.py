# SPDX-License-Identifier: Apache-2.0

import aethos_core.providers  # noqa: F401
from aethos_core.catalog.connection_catalog import build_connections_catalog
from aethos_core.providers.base.provider_registry import ProviderRegistry


def test_connections_catalog_includes_vercel_railway_github_registered():
    catalog = build_connections_catalog()
    connected_names = {p["name"] for p in catalog["connected_providers"]}
    assert "vercel" in connected_names
    assert "railway" in connected_names
    assert "github" in connected_names
    available_names = {p["name"] for p in catalog["available_providers"]}
    assert "railway" not in available_names
    assert "github" not in available_names
    assert catalog["available_channels"] or catalog["connected_channels"]


def test_railway_capabilities_registered_readonly_enabled():
    railway = ProviderRegistry.get("railway")
    github = ProviderRegistry.get("github")
    assert railway is not None
    assert github is not None
    readonly_enabled = [op for op, cap in railway.capabilities.items() if cap.enabled and not cap.mutation]
    assert "list_deployments" in readonly_enabled
    assert "why_down" in readonly_enabled
    github_readonly = [op for op, cap in github.capabilities.items() if cap.enabled and not cap.mutation]
    assert "workflow_runs" in github_readonly
    assert github.mutation_adapter is not None
    assert railway.mutation_adapter is not None
    assert railway.mutation_adapter.enabled is False
    assert github.mutation_adapter.enabled is False
