# SPDX-License-Identifier: Apache-2.0
"""Recommendation followups — natural continuation."""

from __future__ import annotations

from aethos_core.conversation.synthesis_pkg.conversational_recovery import append_followups


def add_followups(text: str, *, include: bool = True) -> str:
    if not include:
        return text
    if "If you'd like" in text:
        return text
    return append_followups(text)
