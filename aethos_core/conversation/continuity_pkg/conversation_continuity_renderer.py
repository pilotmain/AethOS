# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — continuity dashboard renderer."""

from __future__ import annotations

from typing import Any


def render_conversation_continuity_markdown(*, payload: dict[str, Any], focus: str = "continuity_dashboard") -> str:
    sections = payload.get("sections") or {}
    dashboard = sections.get("continuity_dashboard") or {}
    lines = [
        "## Continuity dashboard",
        "",
        f"- Active topic: **{dashboard.get('active_topic') or '—'}**",
        f"- Parent topic: **{dashboard.get('parent_topic') or '—'}**",
        f"- Active mode: **{dashboard.get('active_mode') or 'general'}**",
        f"- Turn count: **{dashboard.get('turn_count', 0)}**",
        f"- Human-support persistence: **{'on' if dashboard.get('human_support_persistence') else 'off'}**",
        f"- Operational persistence: **{'on' if dashboard.get('operational_persistence') else 'off'}**",
        f"- Topic drift detected: **{'yes' if dashboard.get('topic_drift_detected') else 'no'}**",
        "",
        "## Session truth",
        "",
        str((sections.get("session_truth_registry") or {}).get("conversation_context_is_session_scoped")),
        "",
        "Conversation context is session-scoped — not long-term memory.",
    ]
    return "\n".join(lines)
