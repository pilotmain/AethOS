# SPDX-License-Identifier: Apache-2.0
"""Session linking — map Telegram and Mission Control continuity keys."""

from __future__ import annotations

from typing import Any


def link_session_surfaces(*, session_id: str = "default", channel: str = "chat") -> dict[str, Any]:
    """Resolve linked continuity keys across chat surfaces."""
    from aethos_core.channels.session_alias import get_session_group, resolve_canonical_session_id

    sid = (session_id or "default").strip() or "default"
    canonical = resolve_canonical_session_id(sid)
    group = get_session_group(sid)
    linked = list(dict.fromkeys(group.get("linked_session_ids") or [sid]))
    surfaces: list[str] = []

    for row in linked:
        if str(row).startswith("tg-"):
            surfaces.append("telegram")
        elif str(row).startswith("sess-") or str(row).startswith("web-"):
            surfaces.append("web_chat")
    if channel in {"telegram", "chat"} or channel.startswith("tg"):
        if "web_chat" not in surfaces and not sid.startswith("tg-"):
            surfaces.append("web_chat")
    if sid.startswith("tg-"):
        surfaces.append("telegram")
    if not surfaces:
        surfaces.append("mission_control" if channel not in {"telegram", "chat"} else "web_chat")

    return {
        "primary_session": sid,
        "canonical_session_id": canonical,
        "linked_sessions": linked,
        "active_surfaces": list(dict.fromkeys(surfaces)),
        "summary": f"Session linked across {', '.join(surfaces) or 'session'}.",
    }
