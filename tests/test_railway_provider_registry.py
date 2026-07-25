# SPDX-License-Identifier: Apache-2.0

import aethos_core.providers  # noqa: F401
from aethos_core.providers.base.provider_registry import ProviderRegistry
from aethos_core.providers.railway.operations.readonly_execution import RailwayReadonlyExecutionAdapter
from aethos_core.providers.railway.provider import ensure_railway_registered


def test_railway_registered_with_readonly_factory():
    spec = ensure_railway_registered()
    assert spec.name == "railway"
    assert spec.readonly_execution_factory is not None
    assert ProviderRegistry.get("railway") is spec


def test_railway_readonly_adapter_contract():
    adapter = RailwayReadonlyExecutionAdapter("token", credential_id="cred-1")
    assert adapter.provider == "railway"
