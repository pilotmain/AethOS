# SPDX-License-Identifier: Apache-2.0
"""Per-provider model selection API — choose which models each provider exposes.

Mounted under /api/v1. The enabled set + custom model ids persist in the runtime
config store (not .env); keys stay in the vault. The model picker and arbiter read
exactly the user's enabled models.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from aethos_core.llm.model_selection import (
    get_provider_model_selection,
    list_provider_model_selections,
    set_provider_model_selection,
)

router = APIRouter(tags=["model-selection"])


def _actor(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user:
        return str(user.get("email") or user.get("user_id") or "operator")
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    tenant = get_current_tenant()
    return tenant if tenant != DEFAULT_TENANT else "operator"


class ModelSelectionRequest(BaseModel):
    enabled_ids: list[str] = Field(default_factory=list)
    custom_ids: list[str] = Field(default_factory=list)


@router.get("/models/providers")
def list_model_selections() -> dict[str, object]:
    return {"ok": True, "providers": list_provider_model_selections()}


@router.get("/models/providers/{provider}")
def get_model_selection(provider: str) -> dict[str, object]:
    sel = get_provider_model_selection(provider)
    if sel is None:
        raise HTTPException(status_code=404, detail=f"{provider} is not a known model provider.")
    return {"ok": True, **sel}


@router.post("/models/providers/{provider}")
def update_model_selection(provider: str, req: ModelSelectionRequest, request: Request) -> dict[str, object]:
    try:
        sel = set_provider_model_selection(
            provider,
            enabled_ids=req.enabled_ids,
            custom_ids=req.custom_ids,
            actor=_actor(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"ok": True, **sel}
