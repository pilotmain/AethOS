# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["mutations"])


@router.get("/mutations/{job_id}")
def get_mutation_job_api(job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.mutation_execution_runtime import get_mutation_job_truth

    result = get_mutation_job_truth(job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("reason", "job_not_found"))
    return result


@router.get("/mutations/{job_id}/audit")
def get_mutation_job_audit_api(job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.mutation_execution_runtime import get_mutation_job_audit

    result = get_mutation_job_audit(job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=result.get("reason", "audit_not_found"))
    return result


@router.get("/mutations/{job_id}/verification")
def get_mutation_job_verification_api(job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.mutation_execution_runtime import get_mutation_job_verification

    return get_mutation_job_verification(job_id)


@router.post("/mutations/{job_id}/execute")
def post_execute_mutation_job_api(job_id: str) -> dict[str, Any]:
    from aethos_core.jobs.mutation_execution_runtime import execute_mutation_job

    result = execute_mutation_job(job_id)
    if not result.get("ok"):
        raise HTTPException(status_code=409, detail=result.get("reason", "execute_failed"))
    return result
