# SPDX-License-Identifier: Apache-2.0
"""Provider diagnosis runtime."""

from __future__ import annotations

from aethos_core.provider_skills.runtime import diagnose_provider_job


def diagnose_job(*, job_id: str) -> dict[str, object]:
    return diagnose_provider_job(job_id=job_id)
