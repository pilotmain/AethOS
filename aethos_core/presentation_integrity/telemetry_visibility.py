# SPDX-License-Identifier: Apache-2.0
"""Telemetry visibility — hide runtime telemetry."""

from __future__ import annotations

import re


def suppress_telemetry(text: str, *, mode: str = "casual") -> str:
    if mode in ("engineering", "operator", "debug"):
        return text
    text = re.sub(r"\b(?:overall\s+)?confidence\s*:\s*(?:medium|high|low)\s*/\s*0\.\d+\b", "", text, flags=re.I)
    text = re.sub(r"\bfreshness\s*:\s*0\.\d+\b", "", text, flags=re.I)
    text = re.sub(r"\bsource agreement\s*:\s*0\.\d+\b", "", text, flags=re.I)
    return text.strip()
