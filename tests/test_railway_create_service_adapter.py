# SPDX-License-Identifier: Apache-2.0
"""FIX 108 — governed Railway create_service adapter (mocked GraphQL)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.provider_discovery.provider_inventory import (
    ProviderEnvironmentRecord,
    ProviderInventory,
    ProviderProjectRecord,
    ProviderServiceRecord,
)
from aethos_core.providers.railway.greenfield_adapters.create_service_adapter import (
    create_railway_service,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
    live_create_service_authorization,
)
from aethos_core.providers.railway.greenfield_adapters.service_create_graphql import (
    invoke_service_create,
)


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _inventory(*, existing_service: str = "") -> ProviderInventory:
    services = []
    if existing_service:
        services.append(ProviderServiceRecord(name=existing_service, id="svc-existing"))
    return ProviderInventory(
        provider="railway",
        projects=[
            ProviderProjectRecord(
                id="proj-1",
                name="pilotos",
                environments=[
                    ProviderEnvironmentRecord(
                        id="env-staging",
                        name="staging",
                        services=services,
                    )
                ],
            )
        ],
    )


def test_invoke_service_create_success():
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.service_create_graphql.graphql_query",
        return_value={"ok": True, "data": {"serviceCreate": {"id": "svc-new", "name": "api"}}},
    ):
        out = invoke_service_create(
            "token",
            project_id="proj-1",
            service_name="api",
            environment_id="env-staging",
        )
    assert out["ok"] is True
    assert out["service_id"] == "svc-new"


def test_create_railway_service_rejects_unauthorized_call():
    result = create_railway_service(
        project_name="pilotos",
        environment_name="staging",
        service_name="aethos-api",
        idempotency_key="idem-0",
    )
    assert result.ok is False
    assert any("authorization" in err.lower() for err in result.errors)


def test_create_railway_service_performs_mutation_in_staging():
    with (
        patch.dict(
            "os.environ",
            {
                "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
                "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            },
            clear=False,
        ),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.create_service_adapter.resolve_railway_mutation_credentials",
            return_value=("tok", "env", None),
        ),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.target_resolution.discover_railway_inventory",
            return_value=_inventory(),
        ),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.create_service_adapter.invoke_service_create",
            return_value={
                "ok": True,
                "service_id": "svc-108",
                "service_name": "aethos-api",
                "detail": "serviceCreate succeeded",
            },
        ) as mock_create,
    ):
        get_settings.cache_clear()
        with live_create_service_authorization():
            result = create_railway_service(
                project_name="pilotos",
                environment_name="staging",
                service_name="aethos-api",
                idempotency_key="idem-1",
            )

    assert result.ok is True
    assert result.mutation_performed is True
    assert result.service_id == "svc-108"
    mock_create.assert_called_once()


def test_create_railway_service_blocks_non_staging_environment():
    with (
        patch.dict(
            "os.environ",
            {
                "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
                "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            },
            clear=False,
        ),
        live_create_service_authorization(),
    ):
        get_settings.cache_clear()
        result = create_railway_service(
            project_name="pilotos",
            environment_name="development",
            service_name="aethos-api",
            idempotency_key="idem-2",
        )
    assert result.ok is False
    assert result.mutation_performed is False
    assert any("FIX 108" in err for err in result.errors)


def test_create_railway_service_idempotent_when_service_exists():
    with (
        patch.dict(
            "os.environ",
            {
                "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
                "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            },
            clear=False,
        ),
        live_create_service_authorization(),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.create_service_adapter.resolve_railway_mutation_credentials",
            return_value=("tok", "env", None),
        ),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.target_resolution.discover_railway_inventory",
            return_value=_inventory(existing_service="aethos-api"),
        ),
        patch(
            "aethos_core.providers.railway.greenfield_adapters.create_service_adapter.invoke_service_create",
        ) as mock_create,
    ):
        get_settings.cache_clear()
        result = create_railway_service(
            project_name="pilotos",
            environment_name="staging",
            service_name="aethos-api",
            idempotency_key="idem-3",
        )

    assert result.ok is True
    assert result.mutation_performed is False
    assert result.idempotent_replay is True
    assert result.service_id == "svc-existing"
    mock_create.assert_not_called()


def test_create_railway_service_journal_replay_skips_api():
    with (
        patch.dict(
            "os.environ",
            {
                "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
                "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            },
            clear=False,
        ),
        live_create_service_authorization(),
    ):
        get_settings.cache_clear()
        result = create_railway_service(
            project_name="pilotos",
            environment_name="staging",
            service_name="aethos-api",
            idempotency_key="idem-4",
            existing_service_id="svc-prior",
        )
    assert result.ok is True
    assert result.idempotent_replay is True
    assert result.service_id == "svc-prior"
    assert result.mutation_performed is False
