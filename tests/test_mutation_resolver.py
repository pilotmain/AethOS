# SPDX-License-Identifier: Apache-2.0
"""Unified mutation target resolution tests."""

from __future__ import annotations

import pytest

from aethos_core.deployment_targets.mutation_resolver import (
    enrich_mutation_params,
    resolve_mutation_target,
)


def test_registry_resolves_killit():
    row = resolve_mutation_target("killit")
    assert row.resolved
    assert row.provider == "vercel"
    assert row.target_name == "killit"
    assert row.match_source == "deployment_target_registry"


def test_registry_resolves_invoicepilot_alias():
    row = resolve_mutation_target("invoicepilot")
    assert row.resolved
    assert row.provider == "vercel"
    assert row.target_name == "invoicepilot"


def test_registry_resolves_pilot_command_center():
    row = resolve_mutation_target("pilot-command-center")
    assert row.resolved
    assert row.provider == "vercel"


def test_unregistered_target_not_found(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.deployment_targets.registry.find_target_by_alias",
        lambda _alias: None,
    )
    monkeypatch.setattr(
        "aethos_core.operations.orchestration.provider_inference.find_target_in_vercel_inventory",
        lambda _hint: None,
    )
    monkeypatch.setattr(
        "aethos_core.operations.orchestration.provider_inference.find_target_in_railway_inventory",
        lambda _hint: None,
    )
    row = resolve_mutation_target("unknown-service-xyz")
    assert not row.resolved
    assert "registry" in (row.detail or "").lower()


def test_exact_vercel_inventory_when_not_in_registry(monkeypatch):
    monkeypatch.setattr(
        "aethos_core.deployment_targets.registry.find_target_by_alias",
        lambda _alias: None,
    )
    monkeypatch.setattr(
        "aethos_core.operations.orchestration.provider_inference.find_target_in_vercel_inventory",
        lambda hint: {"name": "wingman", "source": "vercel_inventory"} if hint == "wingman" else None,
    )
    row = resolve_mutation_target("wingman", preferred_provider="vercel")
    assert row.resolved
    assert row.provider == "vercel"
    assert row.target_name == "wingman"


def test_enrich_mutation_params_attaches_registry_metadata():
    row = resolve_mutation_target("killit")
    params = enrich_mutation_params({"operation_type": "stop"}, row)
    assert params["provider"] == "vercel"
    assert params["vercel_project"] == "killit"
    assert params["deployment_target_alias"] == "killit"
