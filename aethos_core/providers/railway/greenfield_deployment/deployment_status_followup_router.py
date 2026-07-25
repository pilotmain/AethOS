# SPDX-License-Identifier: Apache-2.0
"""Route natural-language Railway deployment status follow-ups after solo greenfield deploy."""

from __future__ import annotations

import re

_STATUS_FOLLOWUP_RX = re.compile(
    r"\b("
    r"status update"
    r"|update on"
    r"|what(?:'s| is)\s+(?:the\s+)?(?:deployment\s+)?status"
    r"|deployment status"
    r"|how(?:'s| is)\s+(?:the\s+)?deploy(?:ment)?"
    r"|is it live"
    r"|is it up"
    r")\b",
    re.I,
)
_RAILWAY_RX = re.compile(r"\b(?:railway|rail\s*way|aethos)\b", re.I)
_EXPLICIT_NEW_DEPLOY_RX = re.compile(
    r"\b(deploy\s+aethos|greenfield|with env vars and verify)\b",
    re.I,
)


def is_railway_deployment_status_followup(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or not _STATUS_FOLLOWUP_RX.search(raw):
        return False
    if _EXPLICIT_NEW_DEPLOY_RX.search(raw):
        return False
    from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
        is_railway_greenfield_deployment_intent,
    )

    if is_railway_greenfield_deployment_intent(raw):
        return False
    return True


def route_railway_deployment_status_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if re.search(r"\bvercel\b", raw, re.I):
        return None
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import should_yield_active_thread_for_readonly

    if should_yield_active_thread_for_readonly(raw):
        return None
    if not is_railway_deployment_status_followup(text):
        return None

    from aethos_core.operational_thread_memory.solo_greenfield_thread_memory import (
        compose_greenfield_deployment_status_reply,
        resolve_greenfield_deployment_thread,
    )

    thread = resolve_greenfield_deployment_thread(session_id=session_id)
    if thread is None:
        if _RAILWAY_RX.search(text):
            return (
                "I don't have a recent Railway greenfield deployment in this session yet.\n\n"
                "Run **`Deploy AethOS to Railway with env vars and verify it.`** first, "
                "then ask for a status update.",
                "railway_greenfield_deployment_status_missing",
                {"route_id": "railway_greenfield_deployment_status_followup", "provider": "railway"},
            )
        return None

    return compose_greenfield_deployment_status_reply(thread=thread)
