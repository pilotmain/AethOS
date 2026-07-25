# SPDX-License-Identifier: Apache-2.0
"""Local workspace chat — delegates to engineering intelligence lane."""

from __future__ import annotations

from aethos_core.chat.engineering_intelligence import execute_engineering_intent, is_engineering_intelligence_request


def local_workspace_reply(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    if not is_engineering_intelligence_request(text):
        return None
    return execute_engineering_intent(text, session_id=session_id)
