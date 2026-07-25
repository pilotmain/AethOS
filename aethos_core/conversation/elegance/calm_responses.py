# SPDX-License-Identifier: Apache-2.0
"""Calm responses — emotionally steady replies."""

from __future__ import annotations

import re

_HYPE_RX = re.compile(r"\b(critical|urgent|WARNING|!!!)\b", re.I)


def calm_tone(text: str) -> str:
    return _HYPE_RX.sub("", text).replace("!!", ".").strip()
