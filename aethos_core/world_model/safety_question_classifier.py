# SPDX-License-Identifier: Apache-2.0
"""Strict safety-question classification — not mutation commands."""

from __future__ import annotations

import re

_SAFETY_QUESTION_RX = re.compile(
    r"\b("
    r"is restart safe|should (?:i|we) restart|safe to restart|can i restart|"
    r"is redeploy safe|should (?:i|we) redeploy|safe to redeploy|can i redeploy|"
    r"can we safely restart|is it safe to restart|is it safe to redeploy|"
    r"can we safely redeploy|should we safely restart|should we safely redeploy"
    r")\b",
    re.I,
)


def is_safety_question(text: str) -> bool:
    """True when the user asks about mutation safety rather than commanding one."""
    return bool(_SAFETY_QUESTION_RX.search((text or "").strip()))
