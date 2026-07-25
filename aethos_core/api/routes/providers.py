# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["providers"])


@router.get("/providers")
def list_providers() -> dict[str, Any]:
    import aethos_core.providers  # noqa: F401 — bootstrap registry

    from aethos_core.providers.base.provider_registry import ProviderRegistry

    catalog = ProviderRegistry.public_catalog()
    return {"providers": catalog, "count": len(catalog)}


@router.get("/providers/{provider_name}/capabilities")
def get_provider_capabilities(provider_name: str) -> dict[str, Any]:
    import aethos_core.providers  # noqa: F401

    from aethos_core.providers.base.provider_registry import ProviderRegistry

    spec = ProviderRegistry.get(provider_name)
    if spec is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider_name}")
    return {
        "provider": spec.name,
        "label": spec.label,
        "capabilities": spec.capability_dicts(),
    }


@router.get("/providers/railway/targets")
def get_railway_targets(limit: int = 20) -> dict[str, Any]:
    from aethos_core.jobs.target_resolution import refresh_railway_targets

    return refresh_railway_targets(limit=limit)
