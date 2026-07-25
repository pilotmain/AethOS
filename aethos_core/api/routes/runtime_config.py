# SPDX-License-Identifier: Apache-2.0
"""Runtime configuration API — UI-writable, allowlisted settings (no .env needed).

Mounted under /api/v1. Reads return current effective values + source; writes go
through the §3 guardrails (allowlist, no secrets, no governance flags, audited).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from aethos_core.runtime_config.effective_settings import (
    ConfigWriteError,
    list_effective_settings,
    revert_effective_setting,
    set_effective_setting,
)

router = APIRouter(tags=["runtime-config"])


class ConfigWriteRequest(BaseModel):
    value: object


def _actor(request: Request) -> str:
    """Real acting user for audit (email/user_id), not the literal 'operator'."""
    user = getattr(request.state, "user", None)
    if user:
        return str(user.get("email") or user.get("user_id") or "operator")
    from aethos_core.tenancy import DEFAULT_TENANT, get_current_tenant

    tenant = get_current_tenant()
    return tenant if tenant != DEFAULT_TENANT else "operator"


@router.get("/config")
def get_runtime_config() -> dict[str, object]:
    """Grouped current effective values + metadata for the Settings surface."""
    return list_effective_settings()


@router.post("/config/{key}")
def set_runtime_config(key: str, req: ConfigWriteRequest, request: Request) -> dict[str, object]:
    try:
        return set_effective_setting(key, req.value, actor=_actor(request))
    except ConfigWriteError as exc:
        status = 404 if exc.code == "unknown_key" else 403 if exc.code in {"secret_not_allowed", "operator_only"} else 422
        raise HTTPException(status_code=status, detail={"error": exc.code, "message": exc.message}) from exc


@router.delete("/config/{key}")
def revert_runtime_config(key: str, request: Request) -> dict[str, object]:
    try:
        return revert_effective_setting(key, actor=_actor(request))
    except ConfigWriteError as exc:
        raise HTTPException(status_code=404, detail={"error": exc.code, "message": exc.message}) from exc
