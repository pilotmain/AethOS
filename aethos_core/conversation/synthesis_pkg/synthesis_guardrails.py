# SPDX-License-Identifier: Apache-2.0
"""Synthesis guardrails — prevent noisy output."""

from __future__ import annotations

import re
from typing import Any

_TELEMETRY_RX = re.compile(
    r"(overall confidence|freshness|source agreement)\s*:\s*\*?\*?\d+\.?\d*",
    re.I,
)
_RAW_CONF_RX = re.compile(r"\b(medium|high|low)\s*/\s*0\.\d+\b", re.I)


def guard_output(text: str) -> dict[str, Any]:
    issues: list[str] = []
    if _TELEMETRY_RX.search(text):
        issues.append("raw_telemetry")
    if _RAW_CONF_RX.search(text):
        issues.append("raw_confidence_ratio")
    if re.search(r"\b(re|rart|rrun)-[a-f0-9]{6,}\b", text, re.I):
        issues.append("internal_ids")
    if re.search(r"^##\s*(Artifacts|Limitations)\s*$", text, re.M | re.I):
        issues.append("engineering_sections")
    return {"clean": not issues, "issues": issues}
