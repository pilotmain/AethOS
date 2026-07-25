# SPDX-License-Identifier: Apache-2.0
"""FIX 142 — chat intent for operator contextual guidance."""

from __future__ import annotations

import re

_GUIDANCE_RX = re.compile(
    r"\b("
    r"operator\s+(?:recommendations?|guidance)"
    r"|contextual\s+(?:operational\s+)?guidance"
    r"|operational\s+copilot"
    r"|what\s+should\s+i\s+do\s+next"
    r"|suggest\s+(?:likely\s+)?next\s+(?:governed\s+)?steps?"
    r"|suggest\s+(?:historical\s+)?mitigations?"
    r"|approval\s+sequencing"
    r"|rollout\s+caution"
    r"|verification\s+gaps?"
    r"|show\s+operator\s+guidance"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b(auto\s+execute|autonomous\s+operation|run\s+this\s+for\s+me|execute\s+recommendations?)\b",
    re.I,
)


def is_operator_guidance_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_GUIDANCE_RX.search(raw))
