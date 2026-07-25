# SPDX-License-Identifier: Apache-2.0
"""Multi-tenant onboarding and usage API (Phase 6)."""

from __future__ import annotations

from fastapi import APIRouter

from aethos_core.tenancy.tenant_metering import get_tenant_usage_summary
from aethos_core.tenancy.tenant_onboarding import build_tenant_onboarding_state, mark_onboarding_complete

router = APIRouter(tags=["tenancy"])


@router.get("/tenancy/onboarding")
def get_tenant_onboarding_api() -> dict[str, object]:
    return build_tenant_onboarding_state()


@router.post("/tenancy/onboarding/complete")
def complete_tenant_onboarding_api() -> dict[str, object]:
    mark_onboarding_complete()
    state = build_tenant_onboarding_state()
    return {"ok": True, **state}


@router.get("/tenancy/usage")
def get_tenant_usage_api(session_id: str | None = None) -> dict[str, object]:
    return get_tenant_usage_summary(session_id=session_id)
