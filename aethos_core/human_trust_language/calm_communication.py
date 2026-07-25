# SPDX-License-Identifier: Apache-2.0
"""Calm communication — emotionally steady phrasing."""

from __future__ import annotations

from aethos_core.conversation.entity_compat import calm_tone


def calm_communication(text: str) -> str:
    return calm_tone(text)
