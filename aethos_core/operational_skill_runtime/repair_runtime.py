# SPDX-License-Identifier: Apache-2.0
"""Provider repair / fix-plan runtime."""

from __future__ import annotations

from aethos_core.provider_skills.runtime import fix_plan_for_job


def propose_repair(*, job_id: str) -> dict[str, object]:
    return fix_plan_for_job(job_id=job_id)
