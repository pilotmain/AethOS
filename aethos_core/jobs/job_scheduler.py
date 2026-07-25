# SPDX-License-Identifier: Apache-2.0
"""Job scheduler — recovery verification windows."""

from __future__ import annotations

from typing import Any

from aethos_core.jobs.job_runtime import create_governed_job

RECOVERY_WINDOWS = (
    ("immediate", 0),
    ("5m", 5),
    ("15m", 15),
    ("delayed", 30),
)


def schedule_recovery_windows(
    *,
    session_id: str = "default",
    subject: str = "Railway deployment recovery",
    windows: tuple[tuple[str, int], ...] | None = None,
) -> list[dict[str, Any]]:
    """Schedule governed recovery verification jobs."""
    scheduled: list[dict[str, Any]] = []
    for label, delay_sec in windows or RECOVERY_WINDOWS:
        job = create_governed_job(
            job_type="recovery_window_check",
            session_id=session_id,
            entity_name="Mission Control Analyst",
            params={"window": label, "delay_seconds": delay_sec, "subject": subject[:240]},
            auto_dispatch=True,
        )
        if job.get("ok"):
            scheduled.append(job["job"])
    return scheduled
