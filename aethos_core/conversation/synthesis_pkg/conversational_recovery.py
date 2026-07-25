# SPDX-License-Identifier: Apache-2.0
"""Conversational recovery — graceful uncertainty handling."""

from __future__ import annotations

from typing import Any


def build_recovery_response(*, query: str, reason: str = "limited evidence") -> str:
    return (
        f"I couldn't build a fully confident answer for that yet. "
        f"Based on {reason}, I'd suggest narrowing the request — for example by region, age group, or a specific feature you're looking for."
    )


def append_followups(text: str, *, contract: dict[str, Any] | None = None) -> str:
    lines = [
        text,
        "",
        "If you'd like, I can also narrow this down by:",
        "- toddler-friendly options",
        "- shaded playgrounds",
        "- splash parks",
        "- Northern Virginia only",
        "- playgrounds near you",
    ]
    return "\n".join(lines)
