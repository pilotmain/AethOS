# SPDX-License-Identifier: Apache-2.0
"""Provider connection registry."""

from __future__ import annotations

from typing import Any

import aethos_core.providers  # noqa: F401 — bootstrap registry

from aethos_core.connections.models import ProviderConnectionStatus
from aethos_core.providers.base.provider_registry import ProviderRegistry


def get_auth_adapter(provider: str):
    return ProviderRegistry.get_auth_adapter(provider)


def list_connections() -> dict[str, Any]:
    providers = {}
    for name in ProviderRegistry.list_names():
        adapter = ProviderRegistry.get_auth_adapter(name)
        if adapter is None:
            continue
        providers[name] = adapter.connection_status().to_dict()
    return {"providers": providers, "count": len(providers)}


def get_connection(provider: str) -> ProviderConnectionStatus:
    adapter = get_auth_adapter(provider)
    if adapter is None:
        raise KeyError(provider)
    return adapter.connection_status()
