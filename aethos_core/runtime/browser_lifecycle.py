# SPDX-License-Identifier: Apache-2.0
"""Canonical browser session lifecycle — shared by API, chat, and Mission Control."""

from __future__ import annotations

from enum import Enum


class BrowserSessionStatus(str, Enum):
    QUEUED = "queued"
    APPROVED = "approved"
    LAUNCHING = "launching"
    RUNNING = "running"
    WAITING_FOR_OPERATOR = "waiting_for_operator"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


TERMINAL_STATUSES = frozenset(
    {
        BrowserSessionStatus.COMPLETED,
        BrowserSessionStatus.FAILED,
        BrowserSessionStatus.CANCELLED,
        BrowserSessionStatus.TIMED_OUT,
    }
)

ACTIVE_STATUSES = frozenset(
    {
        BrowserSessionStatus.LAUNCHING,
        BrowserSessionStatus.RUNNING,
        BrowserSessionStatus.WAITING_FOR_OPERATOR,
    }
)


CHAT_BROWSER_EVENT_TYPES = frozenset(
    {
        "session_approved",
        "session_launching",
        "session_running",
        "session_waiting_for_operator",
        "session_completed",
        "session_failed",
        "session_cancelled",
        "session_timed_out",
    }
)


def chat_message_for_session_event(
    *,
    event_type: str,
    target: str,
    status: str,
) -> str:
    """Short chat bubbles only — details live in Mission Control."""
    if event_type == "session_launching":
        return f"⏳ Browser session launching — {target}…"
    if event_type == "session_running":
        return f"🌐 Browser session opened — {target}"
    if event_type == "session_waiting_for_operator":
        return f"⌛ Waiting for operator login — {target}"
    if event_type == "session_completed":
        return f"✅ Browser session completed — {target}"
    if event_type == "session_cancelled":
        return f"🚫 Browser session cancelled — {target}"
    if event_type == "session_timed_out":
        return f"⚠️ Browser session timed out — {target}"
    if event_type == "session_failed":
        return f"⚠️ Browser session failed — {target}"
    return f"Browser session update — {target} ({status})"


def action_approved_browser_message(*, target: str, status_check: bool) -> str:
    if status_check:
        return f"⏳ Browser status check approved for {target}…"
    return f"⏳ Browser session launching — {target}…"


def action_completed_browser_message(
    *,
    target: str,
    session_status: str,
    login_notice: bool,
) -> str:
    if session_status in {"running", "waiting_for_operator"}:
        if login_notice and session_status == "waiting_for_operator":
            return f"🌐 Browser session opened — {target}. Log in manually; AethOS does not store credentials."
        return f"🌐 Browser session opened — {target}"
    if session_status == "completed":
        return f"✅ Browser session completed — {target}"
    return f"✅ Browser action completed — {target}"
