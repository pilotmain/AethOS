# SPDX-License-Identifier: Apache-2.0
"""Map vague operational follow-ups to active thread intents."""

from __future__ import annotations

import re
from typing import Any

_VAGUE_FOLLOWUP_RX = re.compile(
    r"\b("
    r"can you check(?:\s+and\s+report\s+back)?"
    r"|check\s+and\s+report\s+back"
    r"|report\s+back"
    r"|what\s+happened(?:\s+after\s+approval)?"
    r"|why\s+did\s+it\s+fail"
    r"|did\s+it\s+work"
    r"|what\s+is\s+the\s+status"
    r"|what'?s\s+the\s+status"
    r"|what\s+were\s+we\s+talking\s+about"
    r"|what\s+is\s+the\s+status\s+of"
    r"|status\s+update"
    r")\b",
    re.I,
)
_WHY_SERVICE_FAIL_RX = re.compile(r"\bwhy\s+did\s+(.+?)\s+fail\b", re.I)
_STATUS_SERVICE_RX = re.compile(r"\b(?:status|check)\s+(?:of\s+)?(?:the\s+)?([a-z0-9][a-z0-9._-]+)\s+service\b", re.I)


def is_vague_operational_followup(text: str) -> bool:
    from aethos_core.runtime.runtime_config_intent import is_runtime_provider_config_question

    raw = (text or "").strip()
    if is_runtime_provider_config_question(raw):
        return False
    if _VAGUE_FOLLOWUP_RX.search(raw):
        return True
    if _WHY_SERVICE_FAIL_RX.search(raw):
        return True
    return False


def resolve_followup_intent(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    lower = raw.lower()

    if re.search(r"\bwhy\s+did\s+it\s+fail\b", lower):
        return {"kind": "why_failed"}

    why_service = _WHY_SERVICE_FAIL_RX.search(raw)
    if why_service:
        service_phrase = why_service.group(1).strip()
        if service_phrase.lower() not in {"it", "this", "that"}:
            return {"kind": "why_service_failed", "service_phrase": service_phrase}
        return {"kind": "why_failed"}

    if "what were we talking about" in lower or "few seconds before" in lower:
        return {"kind": "thread_recall"}

    if "why did it fail" in lower or "why failed" in lower:
        return {"kind": "why_failed"}

    if "did it work" in lower:
        return {"kind": "did_it_work"}

    if "what happened" in lower or "report back" in lower or "can you check" in lower or "check and report" in lower:
        return {"kind": "check_and_report"}

    if "what is the status" in lower or "what's the status" in lower or "status update" in lower:
        return {"kind": "status_check"}

    status_service = _STATUS_SERVICE_RX.search(raw)
    if status_service:
        return {"kind": "status_check", "service_phrase": status_service.group(1).strip()}

    if _VAGUE_FOLLOWUP_RX.search(raw):
        return {"kind": "check_and_report"}

    return {"kind": "unknown"}
