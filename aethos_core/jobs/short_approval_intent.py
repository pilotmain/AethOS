# SPDX-License-Identifier: Apache-2.0
"""Detect short operational approval replies (no explicit job id)."""

from __future__ import annotations

import re

from aethos_core.jobs.job_approval_guidance import extract_job_id

_SHORT_APPROVAL_PHRASES = frozenset(
    {
        "approve",
        "yes approve",
        "approved",
        "proceed",
        "go ahead",
        "continue",
        "yes continue",
        "run it",
        "execute it",
    }
)

_SHORT_APPROVAL_RX = re.compile(
    r"^(?:yes\s+)?(?:approve[d]?|proceed|go\s+ahead|continue|yes\s+continue|run\s+it|execute\s+it)(?:\s*[.!])?$",
    re.I,
)

_GUIDANCE_BLOCK_RX = re.compile(
    r"\bwhere\b.*\bapprove\b|\bwhy\s+(?:can'?t|cannot)\s+i\s+approve\b|\bwhy\s+is\s+(?:it|this)\s+not\s+approvable\b",
    re.I,
)


def is_short_approval_intent(text: str) -> bool:
    """True when the user is attempting to approve a pending operational job."""
    raw = (text or "").strip()
    if not raw:
        return False
    if _GUIDANCE_BLOCK_RX.search(raw):
        return False

    job_id = extract_job_id(raw)
    if job_id:
        return bool(re.search(r"\b(?:approve[d]?|proceed|go\s+ahead|continue|run\s+it|execute\s+it)\b", raw, re.I))

    normalized = re.sub(r"\s+", " ", raw).strip().lower()
    if normalized in _SHORT_APPROVAL_PHRASES:
        return True
    return bool(_SHORT_APPROVAL_RX.match(normalized))
