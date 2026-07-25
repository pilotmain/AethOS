# SPDX-License-Identifier: Apache-2.0
"""Response intent — new operation vs re-render vs filter."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from aethos_core.response_composition.output_format_classifier import classify_output_format, is_format_only_request

ResponseIntentKind = Literal["new_operation", "rerender", "filter", "fix_priority"]


@dataclass
class ResponseIntent:
    kind: ResponseIntentKind
    output_format: str = "conversational"
    filter_mode: str = "all"
    user_text: str = ""


_FILTER_FAILED_RX = re.compile(
    r"\b(show\s+(?:me\s+)?(?:only\s+)?failed|only\s+failed|failed\s+services?|which\s+services?\s+failed)\b",
    re.I,
)
_FILTER_UNKNOWN_RX = re.compile(r"\b(show\s+(?:me\s+)?unknown|unknown\s+services?|which\s+services?\s+unknown)\b", re.I)
_SHOW_ALL_RX = re.compile(
    r"\b(show\s+all|all\s+services?|full\s+(?:report|inventory)|restore\s+full(?:\s+report)?)\b",
    re.I,
)
_FIX_FIRST_RX = re.compile(
    r"\b(what\s+should\s+i\s+fix\s+first|what\s+to\s+fix\s+first|priority\s+fix(?:es)?)\b",
    re.I,
)
_OPERATION_RX = re.compile(
    r"\b(check|list|show|report|inspect|scan|audit)\b.*\b(all|every|services?|railway|vercel)\b"
    r"|\b(all|every)\b.*\b(services?|apps?)\b",
    re.I,
)


def classify_response_intent(text: str, *, session_id: str = "default") -> ResponseIntent:
    raw = (text or "").strip()
    output_format = classify_output_format(raw)

    if _FIX_FIRST_RX.search(raw):
        return ResponseIntent(kind="fix_priority", output_format=output_format, user_text=raw)

    if _FILTER_FAILED_RX.search(raw):
        return ResponseIntent(kind="filter", output_format=output_format, filter_mode="failed", user_text=raw)
    if _FILTER_UNKNOWN_RX.search(raw):
        return ResponseIntent(kind="filter", output_format=output_format, filter_mode="unknown", user_text=raw)

    if _OPERATION_RX.search(raw):
        return ResponseIntent(kind="new_operation", output_format=output_format, user_text=raw)

    from aethos_core.response_composition.operational_result_store import get_latest_operational_result

    has_prior = get_latest_operational_result(session_id=session_id) is not None

    if has_prior and _SHOW_ALL_RX.search(raw):
        return ResponseIntent(kind="filter", output_format=output_format, filter_mode="all", user_text=raw)

    if has_prior and (is_format_only_request(raw) or (_OPERATION_RX.search(raw) is None and output_format != "conversational")):
        if _OPERATION_RX.search(raw) and output_format != "conversational":
            return ResponseIntent(kind="new_operation", output_format=output_format, user_text=raw)
        return ResponseIntent(kind="rerender", output_format=output_format, user_text=raw)

    if has_prior and output_format != "conversational":
        return ResponseIntent(kind="rerender", output_format=output_format, user_text=raw)

    return ResponseIntent(kind="new_operation", output_format=output_format, user_text=raw)
