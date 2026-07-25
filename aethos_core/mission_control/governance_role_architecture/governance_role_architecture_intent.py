# SPDX-License-Identifier: Apache-2.0
"""FIX 150 — chat intent for governance role architecture."""

from __future__ import annotations

import re

_ROLE_ARCH_RX = re.compile(
    r"\b("
    r"governance\s+role\s+architecture"
    r"|trust\s+boundaries?"
    r"|trust\s+zones?"
    r"|role\s+capability\s+matrix"
    r"|escalation\s+path"
    r"|separation[- ]of[- ]duty"
    r"|review\s+authority\s+scope"
    r"|quorum\s+role\s+composition"
    r"|governance\s+delegation\s+boundaries?"
    r"|institutional\s+responsibility\s+map"
    r"|show\s+governance\s+roles?"
    r"|governance\s+topology"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b("
    r"auto[- ]?elevate\s+role"
    r"|autonomous\s+role"
    r"|delegated\s+execution"
    r"|auto\s+approve"
    r"|mutate\s+policy"
    r")\b",
    re.I,
)


def is_governance_role_architecture_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_ROLE_ARCH_RX.search(raw))
