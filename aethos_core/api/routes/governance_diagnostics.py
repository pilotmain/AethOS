# SPDX-License-Identifier: Apache-2.0
"""Governance diagnostics and MC kill-switch overrides."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=["governance"])


class GovernanceOverrideIn(BaseModel):
    key: str = Field(min_length=1, max_length=80)
    value: bool


@router.get("/governance/diagnostics")
def get_governance_diagnostics_api() -> dict[str, Any]:
    from aethos_core.governance.approval_privacy_governance import governance_diagnostics_snapshot
    from aethos_core.governance.governance_override_store import governance_override_snapshot

    return {
        "ok": True,
        "diagnostics": governance_diagnostics_snapshot(),
        "runtime_overrides": governance_override_snapshot(),
    }


@router.post("/governance/overrides")
def post_governance_override_api(body: GovernanceOverrideIn, request: Request) -> dict[str, Any]:
    from aethos_core.governance.governance_override_store import save_governance_override

    user = getattr(request.state, "user", None)
    try:
        saved = save_governance_override(key=body.key, value=body.value, user=user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"ok": True, "overrides": saved}


@router.get("/governance/pending-operational-approvals")
def get_pending_operational_approvals_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.jobs.pending_job_approval_resolution import list_pending_operational_approvals

    pending = list_pending_operational_approvals(session_id=session_id)
    return {
        "ok": True,
        "session_id": session_id,
        "pending": [
            {
                "job_id": row.job_id,
                "job_type": row.job_type,
                "provider": row.provider,
                "label": row.label,
                "approval_route": row.approval_route,
            }
            for row in pending
        ],
        "count": len(pending),
    }
