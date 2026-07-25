# SPDX-License-Identifier: Apache-2.0
"""Response alignment — remove legacy infrastructure-era wording."""

from __future__ import annotations

import re

_LEGACY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bthis build\b", re.I), "this deployment"),
    (re.compile(r"\btry a capability question\b", re.I), "tell me what you'd like to work through"),
    (re.compile(r"\btry a capability or project-direction question\b", re.I), "share what you'd like to explore"),
    (re.compile(r"\bdeterministic answers?\b", re.I), "governed operational responses"),
    (re.compile(r"\bdeterministic lane\b", re.I), "governed response path"),
    (re.compile(r"\bLane B\b"), "generative intelligence runtime"),
    (re.compile(r"\bLane A\b"), "governed response path"),
    (re.compile(r"\bhost executor\b", re.I), "governed execution runtime"),
    (re.compile(r"\bprovider configured\b", re.I), "operational provider available"),
    (re.compile(r"\bBrowser automation:\s*\*\*on\*\*", re.I), "**Governed browser observation:** available"),
    (re.compile(r"\bBrowser automation:\s*\*\*off\*\*", re.I), "**Governed browser observation:** restricted"),
    (re.compile(r"\bHost executor:\s*\*\*on\*\*", re.I), "**Direct system execution:** available through approval"),
    (re.compile(r"\bHost executor:\s*\*\*off\*\*", re.I), "**Direct system execution:** restricted"),
    (re.compile(r"\*Governed assistance — I recommend and prepare; you approve and execute\.\*", re.I), ""),
)


def align_legacy_phrasing(text: str) -> str:
    """Replace tool-era phrasing with human-centered operational language."""
    out = (text or "").strip()
    for pattern, replacement in _LEGACY_PATTERNS:
        out = pattern.sub(replacement, out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
