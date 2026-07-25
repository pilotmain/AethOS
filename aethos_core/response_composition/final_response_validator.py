# SPDX-License-Identifier: Apache-2.0
"""Final response boundary validation — after wrappers and finalizers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

_JSON_FENCE_RX = re.compile(r"```json\s*\n([\s\S]*?)\n```", re.M)
_UNCLOSED_JSON_FENCE_RX = re.compile(r"```json\s*\n[\s\S]+$", re.M)
_TRUNCATED_END_RX = re.compile(r"[\[{,]\s*$")


@dataclass
class FinalValidationResult:
    ok: bool
    error: str = ""
    parsed_json: Any | None = None


JSON_VALIDATION_FAILURE = (
    "I tried to render the last result as JSON, but the final response failed validation. "
    "I did not emit partial JSON. Please retry JSON format."
)


def extract_json_fence(text: str) -> str | None:
    match = _JSON_FENCE_RX.search(text or "")
    if not match:
        return None
    return match.group(1)


def has_unclosed_json_fence(text: str) -> bool:
    raw = text or ""
    if "```json" not in raw:
        return False
    if _JSON_FENCE_RX.search(raw):
        return False
    return bool(_UNCLOSED_JSON_FENCE_RX.search(raw))


def has_truncated_json_structure(text: str) -> bool:
    raw = extract_json_fence(text)
    if raw is None:
        fence_start = (text or "").find("```json")
        if fence_start >= 0:
            partial = (text or "")[fence_start + len("```json") :].strip()
            return bool(_TRUNCATED_END_RX.search(partial))
        return False
    stripped = raw.rstrip()
    return bool(_TRUNCATED_END_RX.search(stripped))


def validate_json_final_response(text: str) -> FinalValidationResult:
    if has_unclosed_json_fence(text):
        return FinalValidationResult(ok=False, error="unclosed_json_fence")
    if has_truncated_json_structure(text):
        return FinalValidationResult(ok=False, error="truncated_json_structure")
    raw = extract_json_fence(text)
    if raw is None:
        return FinalValidationResult(ok=False, error="missing_json_fence")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return FinalValidationResult(ok=False, error=f"invalid_json:{exc.msg}")
    return FinalValidationResult(ok=True, parsed_json=parsed)


def validate_final_response(text: str, *, output_format: str = "") -> FinalValidationResult:
    if output_format == "json" or "```json" in (text or ""):
        return validate_json_final_response(text)
    if has_unclosed_json_fence(text):
        return FinalValidationResult(ok=False, error="unclosed_json_fence")
    return FinalValidationResult(ok=True)


def finalize_operational_response(body: str, *, output_format: str = "") -> str:
    validation = validate_final_response(body, output_format=output_format)
    if validation.ok:
        return body
    if output_format == "json" or "```json" in body:
        return JSON_VALIDATION_FAILURE
    return body
