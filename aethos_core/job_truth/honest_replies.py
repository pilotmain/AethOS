# SPDX-License-Identifier: Apache-2.0
"""Honest job-status reply composers — Phase 11.8.0."""

from __future__ import annotations

from aethos_core.external_execution_truth.runtime_truth_bridge import compose_external_execution_context
from aethos_core.job_truth.activity_truth import describe_last_activity
from aethos_core.job_truth.freshness_truth import session_freshness
from aethos_core.job_truth.lifecycle_language import describe_job_lifecycle, state_label
from aethos_core.job_truth.notification_policy import compose_notification_digest
from aethos_core.job_truth.progression_truth import bound_progression_confidence
from aethos_core.job_truth.runtime_presence import assess_runtime_presence
from aethos_core.job_truth.stalled_job_handling import describe_stalled_job, is_job_stalled
from aethos_core.jobs.job_memory import build_job_continuity
from aethos_core.jobs.job_notifications import list_pending_notifications, mark_notifications_delivered
from aethos_core.jobs.job_state import list_jobs


def build_job_truth_state(*, session_id: str = "default", now: float | None = None) -> dict[str, object]:
    jobs = list_jobs(session_id=session_id, limit=30)
    continuity = build_job_continuity(session_id=session_id)
    active = continuity.get("active_jobs") or []
    presence = assess_runtime_presence(jobs=jobs, now=now)
    freshness = session_freshness(jobs=jobs, now=now)
    stalled = [j for j in jobs if is_job_stalled(j, now=now)]
    confidence = bound_progression_confidence(
        has_active_jobs=bool(active),
        has_completed_jobs=bool(continuity.get("latest_completed")),
        freshness_tier=str(freshness.get("freshness_tier") or "unknown"),
        stalled_count=len(stalled),
    )
    lifecycle_rows = [describe_job_lifecycle(j, now=now) for j in jobs[:12]]
    pending = list_pending_notifications(session_id=session_id)
    return {
        "ok": True,
        "phase": "11.8.2",
        "session_id": session_id,
        "continuity": continuity,
        "runtime_presence": presence,
        "freshness": freshness,
        "progression_confidence": confidence,
        "stalled_jobs": stalled,
        "lifecycle": lifecycle_rows,
        "pending_notifications": len(pending),
        "canonical_states": list({row["canonical_state"] for row in lifecycle_rows}),
    }


def compose_honest_job_status_reply(*, session_id: str = "default") -> str:
    state = build_job_truth_state(session_id=session_id)
    continuity = state["continuity"]
    if not continuity.get("continuity_available"):
        return "No durable background jobs registered in this session yet."

    presence = state["runtime_presence"]
    lines = [str(presence["summary"])]
    stalled = state.get("stalled_jobs") or []
    if stalled:
        lines.append(describe_stalled_job(stalled[0]))

    active = continuity.get("active_jobs") or []
    if active:
        detail_lines = []
        for job in active[:4]:
            lifecycle = describe_job_lifecycle(job)
            activity = describe_last_activity(job)
            detail_lines.append(
                f"- **{job.get('entity_name') or 'agent'}** — {lifecycle['state_label']} "
                f"({str(job.get('job_type') or 'job').replace('_', ' ')}, last activity {activity['last_activity_phrase']})"
            )
        lines.append("**Job lifecycle:**\n" + "\n".join(detail_lines))
    else:
        latest = continuity.get("latest_completed")
        if latest:
            activity = describe_last_activity(latest)
            lines.append(
                f"Latest completed: **{latest.get('job_type')}** ({latest.get('entity_name') or 'agent'}) — "
                f"{activity['last_activity_phrase']}."
            )

    freshness = state["freshness"]
    if freshness.get("requires_decay_language"):
        lines.append(str(freshness.get("freshness_phrase")))

    conf = state["progression_confidence"]
    lines.append(str(conf.get("phrase")))
    external = compose_external_execution_context(session_id=session_id)
    if external:
        lines.append(external)
    return "\n\n".join(lines)


def compose_honest_progress_inquiry_reply(*, session_id: str = "default", artifact_reply: str | None = None) -> str:
    state = build_job_truth_state(session_id=session_id)
    continuity = state["continuity"]
    presence = state["runtime_presence"]
    active = continuity.get("active_jobs") or []
    stalled = state.get("stalled_jobs") or []
    pending = list_pending_notifications(session_id=session_id)

    if stalled and not active:
        body = describe_stalled_job(stalled[0])
    elif active:
        job = active[0]
        entity = str(job.get("entity_name") or "Operational agent")
        lifecycle = describe_job_lifecycle(job)
        activity = describe_last_activity(job)
        if lifecycle["canonical_state"] in {"verifying", "stabilizing"}:
            body = (
                f"**{entity}** is in **{lifecycle['state_label']}** for "
                f"{str(job.get('job_type') or 'background work').replace('_', ' ')}. "
                f"Last activity {activity['last_activity_phrase']}. "
                "Recovery and verification windows remain bounded — not fake continuous analysis."
            )
        elif lifecycle["canonical_state"] == "running":
            body = (
                f"**{entity}** is **running** a background pass "
                f"({str(job.get('job_type') or 'job').replace('_', ' ')}). "
                f"Last activity {activity['last_activity_phrase']}."
            )
        else:
            body = (
                f"**{entity}** is **{lifecycle['state_label']}** — "
                f"last activity {activity['last_activity_phrase']}."
            )
    elif continuity.get("latest_completed"):
        latest = continuity["latest_completed"]
        entity = str(latest.get("entity_name") or "Operational agent")
        activity = describe_last_activity(latest)
        body = (
            f"**{entity}** completed the latest **{str(latest.get('job_type') or 'job').replace('_', ' ')}** pass "
            f"{activity['last_activity_phrase']}. "
            "No background jobs are actively executing right now."
        )
    elif artifact_reply:
        return artifact_reply
    else:
        body = str(presence["summary"])

    if pending:
        digest = compose_notification_digest(pending)
        if digest:
            body += f"\n\n{digest}"
        mark_notifications_delivered(session_id=session_id)

    freshness = state["freshness"]
    if freshness.get("stale_context"):
        body += f"\n\n{freshness['freshness_phrase']}."

    if artifact_reply and (active or continuity.get("latest_completed")):
        body += f"\n\n{artifact_reply}"

    external = compose_external_execution_context(session_id=session_id)
    if external:
        body += f"\n\n{external}"

    return body
