# SPDX-License-Identifier: Apache-2.0
"""Calm notification batching — Phase 11.8.0."""

from __future__ import annotations

from typing import Any

_LOW_SIGNAL_TYPES = {"recovery_window_check", "provider_verification", "artifact_summarization"}
_HEARTBEAT_PATTERNS = (
    "verification running",
    "verification completed",
    "heartbeat",
    "still thinking",
    "analyzing competitors",
)


def notification_signal_level(*, job_type: str | None, message: str) -> str:
    lower = message.lower()
    if any(p in lower for p in _HEARTBEAT_PATTERNS):
        return "suppress"
    if job_type in _LOW_SIGNAL_TYPES and "failed" not in lower and "regression" not in lower:
        return "low"
    if job_type in {"research_scan", "gtm_synthesis"}:
        return "milestone"
    if "failed" in lower or "regression" in lower or "degraded" in lower:
        return "urgent"
    return "normal"


def should_enqueue_notification(*, job_type: str | None, message: str, pending_count: int = 0) -> bool:
    level = notification_signal_level(job_type=job_type, message=message)
    if level == "suppress":
        return False
    if level == "low" and pending_count >= 2:
        return False
    return True


def compose_notification_digest(notifications: list[dict[str, Any]]) -> str:
    if not notifications:
        return ""
    milestones = [n for n in notifications if notification_signal_level(job_type=n.get("job_type"), message=str(n.get("message") or "")) == "milestone"]
    urgent = [n for n in notifications if notification_signal_level(job_type=n.get("job_type"), message=str(n.get("message") or "")) == "urgent"]
    normal = [n for n in notifications if n not in milestones and n not in urgent]

    parts: list[str] = []
    if urgent:
        parts.append("**Operational attention:** " + _summarize_group(urgent))
    if milestones:
        parts.append("**Latest completed passes:** " + _summarize_group(milestones))
    elif normal:
        parts.append("**Operational update:** " + _summarize_group(normal[:3]))
    if len(notifications) > 1:
        parts.append(
            f"Grouped {len(notifications)} background update(s) into one calm digest — no per-step spam."
        )
    return "\n\n".join(parts)


def _summarize_group(items: list[dict[str, Any]]) -> str:
    labels: list[str] = []
    for item in items[:4]:
        job_type = str(item.get("job_type") or "job").replace("_", " ")
        entity = item.get("entity_name") or item.get("job_id")
        if entity:
            labels.append(f"{job_type} ({entity})")
        else:
            labels.append(job_type)
    if len(items) > 4:
        labels.append(f"+{len(items) - 4} more")
    return ", ".join(labels)


def compose_honest_completion_message(
    *,
    job_type: str,
    entity_name: str | None,
    summary: str,
    last_activity_phrase: str = "just now",
) -> str:
    agent = entity_name or "Operational agent"
    if job_type == "research_scan":
        return (
            f"**{agent}** completed the latest research pass {last_activity_phrase}.\n\n"
            f"{summary}\n\n"
            "Findings are artifact-backed in the active workspace. "
            "The agent is not continuously analyzing — ask for an update when you need the next pass."
        )
    if job_type == "gtm_synthesis":
        return (
            f"**{agent}** completed the latest synthesis pass {last_activity_phrase}.\n\n"
            f"{summary}\n\n"
            "Output is saved to the workspace. "
            "The agent is awaiting the next scheduled refresh unless a new job is queued."
        )
    if job_type == "recovery_window_check":
        return (
            f"Recovery verification completed {last_activity_phrase}.\n\n"
            f"{summary}\n\n"
            "Primary recovery signals remain under sustained verification — "
            "not fully proven until extended stabilization monitoring holds."
        )
    return (
        f"**{agent}** completed a background pass {last_activity_phrase}.\n\n"
        f"{summary}"
    )
