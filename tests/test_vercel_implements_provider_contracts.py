# SPDX-License-Identifier: Apache-2.0

import aethos_core.providers  # noqa: F401
from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.providers.base.readonly_execution_adapter import ReadonlyExecutionAdapter
from aethos_core.providers.base.provider_registry import ProviderRegistry
from aethos_core.providers.vercel.auth import VercelAuthAdapter
from aethos_core.providers.vercel.operations.readonly_execution import VercelReadonlyExecutionAdapter


def test_vercel_auth_implements_provider_auth_contract():
    assert issubclass(VercelAuthAdapter, AuthAdapter)
    adapter = VercelAuthAdapter()
    assert adapter.provider == "vercel"


def test_vercel_readonly_execution_implements_contract():
    assert issubclass(VercelReadonlyExecutionAdapter, ReadonlyExecutionAdapter)
    adapter = VercelReadonlyExecutionAdapter("token", credential_id="cred-1")
    assert adapter.provider == "vercel"


def test_vercel_registered_in_provider_registry():
    spec = ProviderRegistry.get("vercel")
    assert spec is not None
    assert spec.label == "Vercel"
    assert "list_domains" in spec.capabilities
    assert spec.mutation_adapter is not None
    assert spec.mutation_adapter.enabled is False
