# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — chat intent for mission knowledge spaces / semantic retrieval."""

from __future__ import annotations

import re

_KNOWLEDGE_SPACES_RX = re.compile(
    r"\b("
    r"mission\s+knowledge\s+space"
    r"|knowledge\s+space\s+search"
    r"|semantic\s+(?:operational\s+)?search"
    r"|semantic\s+retrieval"
    r"|have\s+we\s+seen\b"
    r"|related\s+missions?"
    r"|operational\s+context\s+recall"
    r"|search\s+operational\s+memory"
    r"|search\s+(?:for\s+)?(?:incidents?|blockers?|approvals?|prs?)"
    r"|historical\s+recommendation"
    r"|organizational\s+(?:operational\s+)?intelligence"
    r")\b",
    re.I,
)

_FORBIDDEN_RX = re.compile(
    r"\b(auto\s+execute|autonomous\s+action|mutate\s+automatically|plan\s+mutation\s+automatically)\b",
    re.I,
)


def is_knowledge_spaces_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _FORBIDDEN_RX.search(raw):
        return False
    return bool(_KNOWLEDGE_SPACES_RX.search(raw))


def extract_knowledge_query(text: str) -> str:
    raw = (text or "").strip()
    for pattern in (
        r"have we seen this before[:\s]*(.+)",
        r"semantic search[:\s]*(.+)",
        r"search operational memory[:\s]*(.+)",
        r"mission knowledge space[:\s]*(.+)",
    ):
        match = re.search(pattern, raw, re.I)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return raw
