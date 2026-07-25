# SPDX-License-Identifier: Apache-2.0
"""Governed Railway greenfield mutation adapters (live API, enabled mode only)."""

__all__ = [
    "ConnectGithubSourceResult",
    "connect_github_source",
    "CreateRailwayServiceResult",
    "create_railway_service",
]


def __getattr__(name: str):
    if name in {"ConnectGithubSourceResult", "connect_github_source"}:
        from aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter import (
            ConnectGithubSourceResult,
            connect_github_source,
        )

        return ConnectGithubSourceResult if name == "ConnectGithubSourceResult" else connect_github_source
    if name in {"CreateRailwayServiceResult", "create_railway_service"}:
        from aethos_core.providers.railway.greenfield_adapters.create_service_adapter import (
            CreateRailwayServiceResult,
            create_railway_service,
        )

        return CreateRailwayServiceResult if name == "CreateRailwayServiceResult" else create_railway_service
    raise AttributeError(name)
