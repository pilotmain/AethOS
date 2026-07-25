# SPDX-License-Identifier: Apache-2.0
"""Chat intent detection for self-improvement (Phase 9.7)."""

from __future__ import annotations

import re

_SELF_IMPROVE_RX = re.compile(
    r"\b("
    r"read\s+open\s+github\s+issues"
    r"|self[\s-]?improvement\s+plan"
    r"|prepare\s+a\s+pr\s+plan"
    r"|github\s+issues\s+for"
    r")\b",
    re.I,
)

_REPO_RX = re.compile(
    r"\b(?:for|on|in)\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b",
    re.I,
)


def is_self_improvement_intent(text: str) -> bool:
    return bool(_SELF_IMPROVE_RX.search((text or "").strip()))


def parse_self_improvement_repository(text: str) -> str | None:
    match = _REPO_RX.search(text or "")
    if match:
        return match.group(1).strip()
    return None
