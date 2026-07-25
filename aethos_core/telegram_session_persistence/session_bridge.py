# SPDX-License-Identifier: Apache-2.0
"""Session bridge — Telegram operational continuity persistence."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.operational_memory import persist_investigation, record_focus_recovery, snapshot_operator_context
from aethos_core.operational_context_memory.context_store import persist_operational_context, recall_operational_context


def _is_telegram(session_id: str) -> bool:
    return session_id.startswith("tg-")


def hydrate_telegram_session(*, session_id: str = "default") -> dict[str, Any]:
    if not _is_telegram(session_id):
        return {"telegram_session": False, "hydrated": False}
    stored = recall_operational_context(session_id=session_id)
    return {
        "telegram_session": True,
        "hydrated": bool(stored),
        "session_id": session_id,
        "latest_investigation": stored.get("latest_investigation"),
        "summary": "Telegram session continuity hydrated." if stored else "Telegram session continuity initialized.",
    }


def persist_telegram_continuity(
    *,
    session_id: str = "default",
    focus: str | None = None,
    investigation: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if focus:
        record_focus_recovery(session_id=session_id, focus=focus, channel="telegram" if _is_telegram(session_id) else "chat")
    if investigation:
        persist_investigation(session_id=session_id, investigation=investigation)
    if investigation:
        from aethos_core.operational_context_memory.investigation_lifecycle import snapshot_investigation

        snapshot_investigation(session_id=session_id, investigation=investigation, status="active", context=context)
    payload = dict(context or {})
    if investigation:
        payload["latest_investigation"] = investigation
    if focus:
        payload["latest_focus"] = focus
    if _is_telegram(session_id):
        payload["channel"] = "telegram"
    if payload:
        persist_operational_context(session_id=session_id, context=payload)
        snapshot_operator_context(session_id=session_id, context=payload)
    return {"ok": True, "session_id": session_id, "persisted": bool(payload)}
