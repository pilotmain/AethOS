# SPDX-License-Identifier: Apache-2.0
"""Discord session identity — align with session_identity parser."""

from __future__ import annotations


def discord_session_id(*, channel_id: str | int, user_id: str | int | None = None) -> str:
    cid = str(channel_id).strip()
    if user_id is not None:
        uid = str(user_id).strip()
        return f"discord-{cid}-{uid}"[:64]
    return f"discord-{cid}"[:64]
