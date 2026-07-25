# SPDX-License-Identifier: Apache-2.0
"""Email/IMAP setup guidance — configuration help, not provider mutations."""

from __future__ import annotations

from aethos_core.chat.informational_turn_classifier import (
    compose_email_imap_setup_guidance_reply,
    is_email_imap_setup_topic,
    is_informational_help_turn,
)


def compose_email_imap_setup_reply_if_applicable(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not raw or not is_email_imap_setup_topic(raw):
        return None
    if not is_informational_help_turn(raw, session_id=session_id):
        return None
    return (
        compose_email_imap_setup_guidance_reply(),
        "email_imap_setup_guidance",
        {"route_id": "email_imap_setup_guidance", "suppress_governance_footer": "true"},
    )
