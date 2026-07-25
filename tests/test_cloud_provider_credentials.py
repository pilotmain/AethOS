# SPDX-License-Identifier: Apache-2.0
"""Cloud provider credential registry and validation."""

from __future__ import annotations

import pytest

from aethos_core.catalog.connection_catalog import PLANNED_PROVIDERS, build_connections_catalog
from aethos_core.connections.credential_hydration import build_credential_center_payload
from aethos_core.providers.base.provider_registry import ProviderRegistry
from aethos_core.providers.cloud.validators import (
    validate_anthropic_token,
    validate_aws_token,
    validate_gcp_token,
    validate_stripe_token,
)


@pytest.fixture(autouse=True)
def _bootstrap_providers():
    import aethos_core.providers  # noqa: F401


def test_credential_managed_providers_include_cloud():
    names = ProviderRegistry.list_credential_managed_names()
    assert "vercel" in names
    assert "railway" in names
    assert "github" in names
    assert "aws" in names
    assert "gcp" in names
    assert "cloudflare" in names
    assert "stripe" in names
    assert len(names) >= 20


def test_public_catalog_includes_credential_ui():
    aws = next(row for row in ProviderRegistry.public_catalog() if row["name"] == "aws")
    assert aws["credential_ui"]["manage_credentials"] is True
    assert aws["credential_ui"]["token_field_label"]


def test_connections_catalog_registers_cloud_providers():
    catalog = build_connections_catalog()
    connected_names = {p["name"] for p in catalog["connected_providers"]}
    assert "aws" in connected_names
    assert "gcp" in connected_names
    assert "cloudflare" in connected_names
    available_names = {p["name"] for p in catalog["available_providers"]}
    assert "aws" not in available_names
    assert "oracle_cloud" not in available_names
    assert "sentry" in {p["name"] for p in catalog["connected_providers"]}


def test_planned_providers_excludes_registered():
    registered = set(ProviderRegistry.list_names())
    for planned in PLANNED_PROVIDERS:
        assert planned["name"] not in registered


def test_formerly_planned_providers_have_credential_ui():
    for name in ("oracle_cloud", "sentry", "twilio", "hetzner"):
        spec = ProviderRegistry.get(name)
        assert spec is not None
        assert spec.credential_ui is not None
        assert spec.credential_ui.manage_credentials is True


def test_credential_center_lists_all_managed_providers():
    payload = build_credential_center_payload()
    providers = {row["provider"] for row in payload["providers"]}
    assert providers == set(ProviderRegistry.list_credential_managed_names())


def test_aws_token_format_validation():
    result = validate_aws_token("AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    if result["ok"]:
        assert "AWS" in result["detail"]
    else:
        assert "STS" in result["detail"] or "failed" in result["detail"].lower()


def test_gcp_service_account_json_validation():
    sample = (
        '{"type":"service_account","project_id":"demo","private_key_id":"abc",'
        '"private_key":"-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n",'
        '"client_email":"demo@demo.iam.gserviceaccount.com","client_id":"123"}'
    )
    result = validate_gcp_token(sample)
    assert result["ok"] is True
    assert "demo@demo.iam.gserviceaccount.com" in result["detail"]


def test_stripe_key_prefix_validation():
    bad = validate_stripe_token("not-a-stripe-key")
    assert bad["ok"] is False
    assert "sk_" in bad["detail"]


def test_anthropic_key_prefix_validation():
    ok = validate_anthropic_token("sk-ant-api03-demo")
    assert ok["ok"] is True
