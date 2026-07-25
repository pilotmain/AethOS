# SPDX-License-Identifier: Apache-2.0
"""Tests for encrypted deployment env value store."""

from __future__ import annotations

import pytest

from aethos_core.providers.railway.env_value_readiness.deployment_env_store import (
    clear_deployment_env_store_for_tests,
    register_deployment_env_value,
    resolve_deployment_env_value,
)
from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
    resolve_env_var_from_secure_store,
)
from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    clear_deployment_env_presence_for_tests,
    probe_env_var_presence,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_deployment_env_store_for_tests()
    clear_deployment_env_presence_for_tests()
    yield
    clear_deployment_env_store_for_tests()
    clear_deployment_env_presence_for_tests()


def test_register_and_resolve_deployment_env_value() -> None:
    target_key = "pilotmain/killit|killit|production|"
    register_deployment_env_value(
        target_key=target_key,
        name="NEXT_PUBLIC_SUPABASE_URL",
        value="https://abc123.supabase.co",
    )
    resolved = resolve_deployment_env_value(
        target_key=target_key,
        name="NEXT_PUBLIC_SUPABASE_URL",
    )
    assert resolved == "https://abc123.supabase.co"


def test_secure_resolution_uses_deployment_store() -> None:
    plan = {
        "repo": "pilotmain/killit",
        "project": "killit",
        "environment": "production",
        "service_name": "",
    }
    target_key = "pilotmain/killit|killit|production|"
    register_deployment_env_value(
        target_key=target_key,
        name="NEXT_PUBLIC_SUPABASE_ANON_KEY",
        value="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.signature",
    )
    presence = probe_env_var_presence("NEXT_PUBLIC_SUPABASE_ANON_KEY", plan=plan)
    assert presence.get("present") is True
    assert presence.get("source") == "secure_store_reference"

    resolved = resolve_env_var_from_secure_store("NEXT_PUBLIC_SUPABASE_ANON_KEY", plan=plan)
    assert resolved.ok is True
    assert resolved.source == "secure_store_reference"
    assert resolved.value.startswith("eyJ")
