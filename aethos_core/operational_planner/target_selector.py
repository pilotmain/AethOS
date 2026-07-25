# SPDX-License-Identifier: Apache-2.0
"""Target selection for operational queries."""

from __future__ import annotations

import re

_TARGET_RX = re.compile(
    r"\b(?:for|on|service|target)\s+([a-z0-9][a-z0-9-]{1,62})\b|\b([a-z0-9][a-z0-9-]{1,62})\-(?:api|web|worker|bot)\b",
    re.I,
)


def select_target(text: str, *, session_id: str = "default", scope: str = "unknown") -> str | None:
    if scope in {"provider_wide", "all_providers", "workspace_wide"}:
        return None

    if scope == "active_target":
        from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

        thread = get_active_operational_thread(session_id)
        if thread is not None:
            return str(getattr(thread, "service", "") or "")

    match = _TARGET_RX.search(text or "")
    if match:
        return match.group(1) or match.group(2)
    return None
