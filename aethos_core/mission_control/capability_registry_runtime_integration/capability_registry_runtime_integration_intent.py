# SPDX-License-Identifier: Apache-2.0
"""FIX 296 — capability registry runtime integration intent."""

from __future__ import annotations

import re

_GENERAL_CAPABILITY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*what\s+can\s+(?:you|aethos)\s+do\??\s*$", re.IGNORECASE),
    re.compile(
        r"^\s*what\s+(?:are\s+you|can\s+you)\s+capable(?:\s+of(?:\s+doing)?)?\??\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*what\s+is\s+(?:implemented|operational|trusted|experimental|planned)\??\s*$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*what\s+(?:providers?\s+do\s+you\s+support|can(?:\s+you)?\s+not\s+do)\??\s*$",
        re.IGNORECASE,
    ),
)

_E2E_PROVIDER_RX = re.compile(
    r"\b("
    r"which\s+(?:cloud(?:\s+env|\s+environment)?|provider|providers)"
    r"|work\s+(?:end[\s-]to[\s-]end|e2e)\s+today"
    r"|end[\s-]to[\s-]end\s+today"
    r"|most\s+complete\s+(?:provider|cloud)"
    r")\b",
    re.IGNORECASE,
)


def is_general_capability_question(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _E2E_PROVIDER_RX.search(raw):
        return False
    return any(pattern.match(raw) for pattern in _GENERAL_CAPABILITY_PATTERNS)
