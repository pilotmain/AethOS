# SPDX-License-Identifier: Apache-2.0
"""Credential requirement API — guidance and runtime refresh."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["credentials"])


class CredentialRefreshIn(BaseModel):
    job_id: str | None = Field(default=None, max_length=64)


@router.get("/credentials/requirements/{job_id}")
def get_credential_requirements(job_id: str) -> dict[str, Any]:
    from aethos_core.credentials.credential_guidance import build_credential_requirements_for_job

    payload = build_credential_requirements_for_job(job_id.strip())
    if not payload:
        raise HTTPException(status_code=404, detail="No credential requirements for this job.")
    return payload


@router.post("/credentials/refresh")
def post_refresh_credentials(body: CredentialRefreshIn | None = None) -> dict[str, Any]:
    from aethos_core.connections.credential_hydration import reload_credential_runtime
    from aethos_core.credentials.credential_guidance import rerun_mutation_preflight_for_job

    report = reload_credential_runtime(validate=True)
    result: dict[str, Any] = {"ok": True, "hydration": report}
    job_id = (body.job_id if body else None) or None
    if job_id:
        result["preflight_rerun"] = rerun_mutation_preflight_for_job(job_id.strip())
    return result
