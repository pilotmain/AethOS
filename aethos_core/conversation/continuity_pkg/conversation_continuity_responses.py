# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — continuity-aware response composers."""

from __future__ import annotations

from aethos_core.conversation.continuity_pkg.conversation_continuity_store import get_session_state


def compose_human_support_follow_up_response(*, session_id: str = "default", topic: str | None = None) -> str:
    state = get_session_state(session_id=session_id)
    active_topic = topic or state.get("active_topic") or "wellbeing"
    topic_copy = {
        "depression": "depression or low mood",
        "anxiety": "anxiety",
        "stress": "stress",
        "loneliness": "loneliness",
        "burnout": "burnout",
        "human_support": "what you're feeling",
    }.get(active_topic, active_topic.replace("_", " "))

    return "\n".join(
        [
            f"Continuing on **{topic_copy}** — here is more gentle guidance:",
            "",
            "Small steps matter. Hydrate, eat something simple if you can, and reduce the scope of what you're asking "
            "yourself to handle today.",
            "",
            "If thoughts feel unsafe or overwhelming, please reach out to local emergency services or a crisis line now. "
            "You deserve support from real people, not just a platform.",
            "",
            "Consider one trusted person, a manager who respects boundaries, or a mental health professional. "
            "You do not need to solve everything at once.",
            "",
            "I'm still here in this same conversation whenever you want to continue — at your pace, without shifting "
            "into operational tasks unless you ask.",
        ]
    )


def compose_topic_continuity_intro(*, session_id: str, body: str) -> str:
    state = get_session_state(session_id=session_id)
    topic = state.get("active_topic")
    if not topic:
        return body
    if body.lstrip().startswith("Continuing"):
        return body
    label = str(topic).replace("_", " ")
    return f"Continuing **{label}**:\n\n{body}"


def compose_conversation_recovery_prefix(*, session_id: str, drift_report: dict) -> str:
    state = get_session_state(session_id=session_id)
    topic = state.get("active_topic") or "our previous topic"
    if not drift_report.get("drift_detected"):
        return ""
    return f"I notice we drifted from **{topic}**. Returning to that topic now.\n\n"
