# SPDX-License-Identifier: Apache-2.0
"""Job truth API — Phase 11.8.0."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(tags=["job-truth"])


@router.get("/job-truth/state")
def get_job_truth_state_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.job_truth.runtime import assess_job_truth_runtime

    return assess_job_truth_runtime(session_id=session_id, channel="api")


@router.get("/job-truth/notifications")
def get_job_truth_notifications_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.job_truth.runtime import get_job_truth_notifications

    return get_job_truth_notifications(session_id=session_id)


@router.get("/job-truth/freshness")
def get_job_truth_freshness_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.job_truth.runtime import get_job_truth_freshness

    return get_job_truth_freshness(session_id=session_id)
