# SPDX-License-Identifier: Apache-2.0
"""Chat copy for tracked job creation."""

from __future__ import annotations

from aethos_core.runtime.authority import authority
from aethos_core.runtime.external_jobs import infer_external_health_from_text
from aethos_core.runtime.jobs import infer_job_from_text, infer_provider_job_from_text
from aethos_core.runtime.job_types import uses_external, uses_provider


def _job_created_body(job, *, queued: bool) -> str:
    body = (
        f"Created tracked job `{job.id}`.\n"
        f"**Title:** {job.title}\n"
        f"**Type:** {job.job_type}\n\n"
        "I'll keep progress visible in **Mission Control → Jobs**."
    )
    if uses_provider(job.job_type) or uses_external(job.job_type):
        body += "\n\nLifecycle updates will appear here as the job runs (chat stays responsive)."
    if uses_external(job.job_type):
        body += (
            "\n\nI'll check available **Vercel health sources** (public status; no login) "
            "and keep the full report in **Mission Control → Jobs**."
        )
        if job.params.get("browser_requested"):
            body += (
                "\n\n**Note:** Authenticated dashboard review is not enabled yet. "
                "This job covers public status and CLI availability only."
            )
    elif queued:
        body += "\n\n⏳ Job queued — cancel from Mission Control → Jobs when needed."
    elif job.status.value == "completed" and uses_provider(job.job_type):
        body += "\n\nSummary will appear here when the job completes. Full report lives in **Mission Control → Jobs**."
    elif job.status.value == "completed" and job.result_preview:
        body += f"\n\n**Preview:** {job.result_preview[:120]}"
    return body


def create_external_health_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]]:
    inferred = infer_external_health_from_text(text)
    if inferred is None:
        title, job_type, params = "Vercel service health check", "external_health_report", {
            "target": "vercel",
            "mode": "public",
            "user_request": text,
            "tool_used": "external_health_report",
        }
    else:
        title, job_type, params = inferred
    job = authority.create_job(
        title=title,
        job_type=job_type,
        params=params,
        source="chat",
        session_id=session_id,
        auto_run=True,
    )
    return (
        _job_created_body(job, queued=job.status.value == "queued"),
        "external_health_job_created",
        {"proposed_job_id": job.id, "proposed_job_type": job.job_type},
    )


def create_provider_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]]:
    inferred = infer_provider_job_from_text(text)
    if inferred is None:
        title, job_type, params = infer_job_from_text(text)
    else:
        title, job_type, params = inferred
    job = authority.create_job(
        title=title,
        job_type=job_type,
        params=params,
        source="chat",
        session_id=session_id,
        auto_run=True,
    )
    return (
        _job_created_body(job, queued=job.status.value == "queued"),
        "provider_job_created",
        {"proposed_job_id": job.id, "proposed_job_type": job.job_type},
    )


def create_tracked_job_reply(
    text: str, *, session_id: str = "default", auto_run: bool = True
) -> tuple[str, str, dict[str, str]]:
    title, job_type, params = infer_job_from_text(text)
    job = authority.create_job(
        title=title,
        job_type=job_type,
        params=params,
        source="chat",
        session_id=session_id,
        auto_run=auto_run,
    )
    return (
        _job_created_body(job, queued=not auto_run),
        "job_created",
        {"proposed_job_id": job.id, "proposed_job_type": job.job_type},
    )


def create_queued_tracked_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]]:
    return create_tracked_job_reply(text, session_id=session_id, auto_run=False)
