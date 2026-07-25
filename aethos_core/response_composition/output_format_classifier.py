# SPDX-License-Identifier: Apache-2.0
"""Output format detection from natural language."""

from __future__ import annotations

import re
from typing import Literal

OutputFormat = Literal[
    "conversational",
    "concise",
    "detailed",
    "table",
    "json",
    "markdown",
    "grouped",
    "executive_summary",
]

_FORMAT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("json", re.compile(r"\b(as\s+)?json\b|\bjson\s+format\b", re.I)),
    ("table", re.compile(r"\b(table\s+format|as\s+a?\s*table|in\s+table\s+format|make\s+it\s+(?:a\s+)?table|table\s+please)\b", re.I)),
    ("executive_summary", re.compile(r"\b(summary\s+only|executive\s+summary|just\s+(?:the\s+)?summary|brief\s+summary)\b", re.I)),
    ("detailed", re.compile(r"\b(full\s+details?|detailed|verbose|everything)\b", re.I)),
    ("grouped", re.compile(r"\bgroup(?:ed)?\s+by\s+project\b|\bby\s+project\b", re.I)),
    ("concise", re.compile(r"\b(concise|short|brief)\b", re.I)),
    ("markdown", re.compile(r"\bmarkdown\s+format\b", re.I)),
]


def detect_output_format(text: str) -> OutputFormat | None:
    raw = (text or "").strip()
    if not raw:
        return None
    for fmt, rx in _FORMAT_PATTERNS:
        if rx.search(raw):
            return fmt  # type: ignore[return-value]
    return None


def classify_output_format(text: str, *, default: OutputFormat = "conversational") -> OutputFormat:
    detected = detect_output_format(text)
    return detected if detected is not None else default


def is_format_only_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or len(raw.split()) > 12:
        return False
    if detect_output_format(raw) is not None:
        return True
    return bool(
        re.search(
            r"^(?:please\s+)?(?:make\s+it|show\s+it|give\s+it\s+to\s+me)\s+(?:in\s+)?(?:table|json|summary)\b",
            raw,
            re.I,
        )
    )
