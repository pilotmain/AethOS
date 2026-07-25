# SPDX-License-Identifier: Apache-2.0
"""Progression reply shaping — progress-aware conversational responses."""

from __future__ import annotations

import random
from typing import Any

# Per-session rest nudge state — gentle, occasional, never nagging.
_REST_SESSION_STATE: dict[str, dict[str, Any]] = {}


def _current_hour(timezone: str | None) -> int | None:
    from datetime import datetime

    try:
        if timezone:
            from zoneinfo import ZoneInfo

            return datetime.now(ZoneInfo(timezone)).hour
    except Exception:
        pass
    try:
        return datetime.now().hour
    except Exception:
        return None


def _outside_working_hours(hour: int, start: int, end: int) -> bool:
    if start == end:
        return False
    if start < end:
        in_window = start <= hour < end
    else:  # overnight worker (e.g. 22 -> 6)
        in_window = hour >= start or hour < end
    return not in_window


def _rest_context_band(hour: int, start: int, end: int) -> str | None:
    """Time-aware band for rapport nudges — never 'past your hours' in early morning."""
    if 5 <= hour < 8:
        return "early_morning"
    if 1 <= hour < 5:
        return "deep_night"
    if hour == 0 or hour >= 23:
        return "late_night"
    if not _outside_working_hours(hour, start, end):
        return None
    if hour >= end:
        return "late_evening"
    return None


_EARLY_MORNING_POOL = (
    "You're up early, {name} — nice. Let's make it count.",
    "Early start, {name} — I'm here whenever you're ready.",
    "Morning energy, {name}. What are we tackling first?",
)

_LATE_EVENING_POOL = (
    "It's getting late, {name} — happy to keep going, or we can pick this up tomorrow.",
    "Long day, {name}? I'm glad to keep going — or we can pause and resume when you're ready.",
    "It's past your usual hours, {name} — your call whether we keep going or pick this up later.",
)

_LATE_NIGHT_POOL = (
    "It's pretty late, {name} — no pressure, but rest is allowed.",
    "Getting late out there, {name}. I'm here if you need me — resting is okay too.",
)

_DEEP_NIGHT_POOL = (
    "Okay {name}, *really* — go get some sleep. I'll be right here tomorrow.",
    "{name}, it's deep into the night. I'll keep this ready — sleep is allowed.",
)


def _pick_nudge_message(band: str, name: str, escalation: int) -> str:
    who = name or "friend"
    if band == "early_morning":
        return random.choice(_EARLY_MORNING_POOL).format(name=who)
    if band == "deep_night" and escalation >= 1:
        return random.choice(_DEEP_NIGHT_POOL).format(name=who)
    if band in {"late_night", "deep_night"}:
        return random.choice(_LATE_NIGHT_POOL).format(name=who)
    return random.choice(_LATE_EVENING_POOL).format(name=who)


def append_optional_rest_hint(reply: str, *, session_id: str = "default") -> str:
    """Legacy rest nudge — retired; deliver-as-is under single-loop (§A1)."""
    _ = session_id
    return reply


def reset_rest_nudge_state_for_tests() -> None:
    _REST_SESSION_STATE.clear()


from aethos_core.execution_progress_tracking.progress_tracker import get_execution_progress
from aethos_core.investigation_output_runtime.output_composer import compose_investigation_output
from aethos_core.operational_artifacts.artifact_store import list_session_artifacts
from aethos_core.operational_entity_runtime.lightweight_agent_registry import get_workspace, list_active_entities
from aethos_core.persistent_workspace_outputs.output_store import set_completion_watch


def compose_agent_conclusion_reply(
    *,
    session_id: str = "default",
    agent_name: str | None = None,
) -> str:
    output = compose_investigation_output(session_id=session_id, agent_name=agent_name, advance=True)
    if not output.get("available"):
        return (
            "No active operational agents in this session yet.\n\n"
            "Initialize agents first, then I can report their evolving findings."
        )
    return str(output.get("reply") or "")


def compose_completion_watch_reply(*, session_id: str = "default") -> str:
    set_completion_watch(session_id=session_id, enabled=True)
    entities = list_active_entities(session_id=session_id)
    names = ", ".join(e.get("name", "entity") for e in entities) or "operational agents"
    output = compose_investigation_output(session_id=session_id, advance=False)
    progress = get_execution_progress(session_id=session_id)
    stage = int(progress.get("progression_stage") or 1)

    if output.get("available") and output.get("reply"):
        return (
            f"I'll track **{names}** and surface evolving findings as they progress.\n\n"
            f"**Current status (stage {stage}):**\n{output['reply']}\n\n"
            "I'll notify you here when conclusions mature — ask anytime for an interim update."
        )

    workspace = get_workspace(session_id=session_id)
    return (
        f"I'll monitor **{names}** within the active operational workspace.\n\n"
        f"Objective: **{workspace.get('objective') or 'on-demand agents from your request'}**.\n"
        "Progress updates appear here — ask anytime for an interim update with last-activity truth."
    )


def compose_progress_inquiry_reply(*, session_id: str = "default", agent_name: str | None = None) -> str:
    from aethos_core.investigation_output_runtime.output_composer import compose_investigation_output
    from aethos_core.job_truth.honest_replies import compose_honest_progress_inquiry_reply

    output = compose_investigation_output(session_id=session_id, agent_name=agent_name, advance=True)
    artifact_reply = str(output["reply"]) if output.get("available") and output.get("reply") else None
    honest = compose_honest_progress_inquiry_reply(session_id=session_id, artifact_reply=artifact_reply)
    if honest:
        return honest
    return compose_continuity_fallback_reply(session_id=session_id)


def compose_job_status_reply(*, session_id: str = "default") -> str:
    from aethos_core.job_truth.honest_replies import compose_honest_job_status_reply

    return compose_honest_job_status_reply(session_id=session_id)


def compose_continuity_fallback_reply(*, session_id: str = "default", user_text: str = "") -> str:
    entities = list_active_entities(session_id=session_id)
    if not entities:
        return ""
    names = ", ".join(e.get("name", "entity") for e in entities)
    workspace = get_workspace(session_id=session_id)
    output = compose_investigation_output(session_id=session_id, advance=False)
    if output.get("available") and output.get("reply"):
        return (
            f"**{names}** remain active in this operational workspace.\n\n"
            f"{output['reply']}"
        )
    artifacts = list_session_artifacts(session_id=session_id)
    if artifacts:
        return (
            f"**{names}** are still progressing.\n\n"
            f"Latest finding: {artifacts[0].get('summary', 'Analysis underway')}.\n\n"
            "Ask what a specific agent has concluded for a deeper read."
        )
    return (
        f"**{names}** are active — objective: **{workspace.get('objective') or 'your assigned objective'}**.\n"
        "Latest artifact-backed findings are available — ask what a specific agent concluded for the current pass."
    )


def compose_progression_workspace_reply(
    *,
    session_id: str = "default",
    entities: list[dict[str, Any]],
    workspace: dict[str, Any],
) -> str:
    if not entities and not workspace:
        return (
            "I don't have an active operational workspace tied to this thread yet.\n\n"
            "Initialize agents first, then I can point you to their accumulated results."
        )

    output = compose_investigation_output(session_id=session_id, advance=False)
    if output.get("available") and output.get("reply"):
        names = ", ".join(e.get("name", "entity") for e in entities)
        artifact = workspace.get("artifact_ref")
        artifact_line = f"\n\nWorkspace artifact: `{artifact}`." if artifact else ""
        return (
            f"**{names}** are active in the operational workspace.\n\n"
            f"{output['reply']}"
            f"{artifact_line}"
        )

    names = ", ".join(e.get("name", "entity") for e in entities) or "operational agents"
    artifacts = list_session_artifacts(session_id=session_id)
    if artifacts:
        latest = artifacts[0].get("summary", "")
        return (
            f"**{names}** are progressing within the active workspace.\n\n"
            f"Latest finding: {latest}\n\n"
            "Ask what a specific agent concluded for deeper output."
        )

    return (
        f"**{names}** are working within the active operational workspace.\n\n"
        f"Objective: **{workspace.get('objective') or 'your assigned objective'}**.\n"
        "Ask what a specific agent concluded in the latest completed pass."
    )
