# SPDX-License-Identifier: Apache-2.0

import aethos_core.providers  # noqa: F401
from aethos_core.operations.orchestration.inventory_dispatch import (
    provider_for_inventory_job,
    resolve_inventory_adapter,
    uses_registry_inventory,
)


def test_inventory_job_provider_mapping():
    assert provider_for_inventory_job("railway_services_inventory") == "railway"
    assert provider_for_inventory_job("github_repositories_inventory") == "github"
    assert provider_for_inventory_job("vercel_projects_inventory") == "vercel"
    assert provider_for_inventory_job("unknown") is None
    assert uses_registry_inventory("github_repositories_inventory") is True


def test_registry_inventory_adapters_registered():
    from aethos_core.providers.github.inventory.inventory_adapter import GitHubInventoryAdapter
    from aethos_core.providers.railway.inventory.inventory_adapter import RailwayInventoryAdapter

    railway = resolve_inventory_adapter("railway")
    github = resolve_inventory_adapter("github")
    assert isinstance(railway, RailwayInventoryAdapter)
    assert isinstance(github, GitHubInventoryAdapter)
    assert railway.provider == "railway"
    assert github.provider == "github"
    assert resolve_inventory_adapter("vercel") is None
