# SPDX-License-Identifier: Apache-2.0
"""Conversational cleanroom — premium conversational output."""

from __future__ import annotations

from aethos_core.presentation_integrity.telemetry_visibility import suppress_telemetry
from aethos_core.presentation_safety.premium_cleanroom import cleanroom_polish


def cleanroom_output(text: str, *, mode: str = "casual") -> str:
    polished = cleanroom_polish(text, mode=mode)
    return suppress_telemetry(polished, mode=mode)
