# SPDX-License-Identifier: Apache-2.0
"""Presence intelligence — operational awareness chat lane."""

from __future__ import annotations

import re

_PRESENCE_RX = re.compile(
    r"\b(what should i pay attention to|what changed|what needs attention|"
    r"ongoing operational risk|recurring deployment|summarize operational|"
    r"any recurring|last \d+ hours?|while i was away|operational brief)\b",
    re.I,
)


def is_presence_intelligence_request(text: str) -> bool:
    return bool(_PRESENCE_RX.search(text or ""))


def execute_presence_intelligence(text: str, *, session_id: str = "default", channel: str = "chat") -> tuple[str, str, dict[str, str]] | None:
    if not is_presence_intelligence_request(text):
        return None
    from aethos_core.presence.collaboration_state import start_collaboration_session
    from aethos_core.presence.presence_runtime import run_presence_cycle, synthesize_operational_brief

    lower = text.lower()
    focus = None
    if "deployment" in lower or "railway" in lower:
        focus = "deployment_debug"
        start_collaboration_session(operator_id=session_id, focus=focus, investigation=text[:120])
    elif "dependency" in lower or "modernization" in lower:
        focus = "dependency_review"
        start_collaboration_session(operator_id=session_id, focus=focus, investigation=text[:120])

    window = 2
    if "away" in lower or "changed" in lower:
        window = 8
    m = re.search(r"last\s+(\d+)\s+hours?", lower)
    if m:
        window = min(int(m.group(1)), 48)

    run_presence_cycle(session_id=session_id, channel=channel)
    body = synthesize_operational_brief(window_hours=window, session_id=session_id, user_text=text)
    return (
        body,
        "operational_presence",
        {
            "lane": "presence_intelligence",
            "window_hours": str(window),
            "focus": focus or "",
            "autonomous_execution_blocked": "true",
        },
    )
