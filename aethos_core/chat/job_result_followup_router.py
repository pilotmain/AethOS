# SPDX-License-Identifier: Apache-2.0
"""Surface completed job artifacts in chat when the user asks for results here."""

from __future__ import annotations

import re

from aethos_core.runtime.jobs import JobStatus, TrackedJob, job_store

_JOB_RESULT_FOLLOWUP_RX = re.compile(
    r"\b("
    r"tell\s+me\b.*\b(?:here|in\s+chat)"
    r"|(?:here|in)\s+chat\s+please"
    r"|just\s+give\s+me\s+the\s+list"
    r"|give\s+me\s+the\s+list\s+here"
    r"|report\s+back"
    r"|health\s+status\s+here"
    r"|summar(?:y|ize).*(?:here|in\s+chat)"
    r"|show\s+(?:me\s+)?(?:the\s+)?(?:results?|report|summary|list)\s+(?:here|in\s+chat)"
    r"|what\s+did\s+(?:the|that)\s+job\s+(?:find|report|show)"
    r")\b",
    re.I,
)


def is_job_result_followup_intent(text: str) -> bool:
    raw = text or ""
    if _JOB_RESULT_FOLLOWUP_RX.search(raw):
        return True
    from aethos_core.operational_session.railway_service_hints import should_route_inline_health_check

    if should_route_inline_health_check(raw):
        return False
    if re.search(r"\b(check|verify)\b.*\bhealth\b", raw, re.I) and re.search(r"\bhealth\b", raw, re.I):
        return False
    if re.search(r"\breport\s+back\b", raw, re.I) and re.search(
        r"\b(check|verify|health|aethos-(?:api|ui))\b", raw, re.I
    ):
        return False
    if re.search(r"\b(restart|redeploy)\b", raw, re.I):
        return False
    if re.search(r"\bhealth\s+check\b", raw, re.I):
        return False
    if re.search(r"\bhealth\b", raw, re.I) and re.search(r"\b(for|run|check)\b", raw, re.I):
        return False
    from aethos_core.execution_brain.agent_provider_cloud import is_agent_provider_cloud_request

    if is_agent_provider_cloud_request(raw):
        return False
    return bool(_JOB_RESULT_FOLLOWUP_RX.search(raw))


def _latest_completed_jobs(*, session_id: str, limit: int = 5) -> list[TrackedJob]:
    rows = [
        job
        for job in job_store.list_all()
        if job.session_id == session_id and job.status == JobStatus.COMPLETED
    ]
    rows.sort(key=lambda job: float(job.updated_at or 0), reverse=True)
    return rows[:limit]


def _extract_bullet_items(body: str, *, max_items: int = 8) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        raw = line.strip()
        if raw.startswith(("- ", "* ")):
            items.append(raw[2:].strip()[:180])
        if len(items) >= max_items:
            break
    return items


def _format_job_artifact(job: TrackedJob) -> str:
    title = job.title or job.job_type.replace("_", " ")
    if job.job_type == "vercel_projects_inventory":
        inv = job.params.get("vercel_inventory") if isinstance(job.params, dict) else None
        if isinstance(inv, dict):
            from aethos_core.chat.vercel_inventory_format import format_vercel_projects_table

            table = format_vercel_projects_table(inv)
            return (
                f"**{title}** (`{job.id}`) — completed.\n\n"
                f"{table}\n\n"
                f"_Full artifact also in Mission Control → Jobs._"
            )
    summary = str(job.result_summary or "").strip()
    body = str(job.full_result or job.result or "").strip()
    lines = [
        f"**{title}** (`{job.id}`) — completed.",
        "",
    ]
    if summary:
        lines.append(f"**Summary:** {summary}")
    bullets = _extract_bullet_items(body, max_items=8) if body else []
    if bullets:
        lines.extend(["", "**Findings:**"])
        lines.extend(f"- {item}" for item in bullets)
    elif body:
        excerpt = "\n".join(line for line in body.splitlines() if line.strip() and not line.startswith("#"))
        excerpt = excerpt.strip()[:1800]
        if excerpt:
            lines.extend(["", excerpt])
    if not summary and not bullets and not body:
        lines.append("The job completed, but no artifact body was stored.")
    return "\n".join(lines)


def compose_job_result_followup_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_job_result_followup_intent(text):
        return None

    jobs = _latest_completed_jobs(session_id=session_id)
    if not jobs:
        return (
            "I do not have a completed job result in this session yet.\n\n"
            "Run a health check or inspection first, then ask me to report it here.",
            "job_result_followup_missing",
            {"route_id": "job_result_followup"},
        )

    sections = [_format_job_artifact(job) for job in jobs[:2]]
    reply = "\n\n---\n\n".join(sections)
    meta = {
        "route_id": "job_result_followup",
        "job_id": jobs[0].id,
        "job_type": jobs[0].job_type,
    }
    return reply, "job_result_followup", meta
