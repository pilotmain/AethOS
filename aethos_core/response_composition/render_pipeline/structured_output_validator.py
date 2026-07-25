# SPDX-License-Identifier: Apache-2.0
"""Validate structured renderer output before emission."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    ok: bool
    parsed: Any | None = None
    error: str = ""


_JSON_FENCE_RX = re.compile(r"```json\s*\n(.*?)\n```", re.S)


def extract_json_fence(text: str) -> str | None:
    match = _JSON_FENCE_RX.search(text or "")
    if not match:
        return None
    return match.group(1)


def validate_json_output(text: str) -> ValidationResult:
    raw = extract_json_fence(text)
    if raw is None:
        return ValidationResult(ok=False, error="missing_json_fence")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return ValidationResult(ok=False, error=f"invalid_json:{exc.msg}")
    return ValidationResult(ok=True, parsed=parsed)


def validate_json_document(document: dict[str, Any]) -> ValidationResult:
    try:
        encoded = json.dumps(document, indent=2, default=str)
        parsed = json.loads(encoded)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return ValidationResult(ok=False, error=str(exc))
    return ValidationResult(ok=True, parsed=parsed)
