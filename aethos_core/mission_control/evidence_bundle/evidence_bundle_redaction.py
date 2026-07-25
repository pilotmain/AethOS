# SPDX-License-Identifier: Apache-2.0
"""FIX 136 — redact secrets from exported evidence bundles."""

from __future__ import annotations

import re
from typing import Any

_SENSITIVE_KEY = re.compile(
    r"(secret|token|password|api[_-]?key|authorization|credential|private[_-]?key|bearer)",
    re.IGNORECASE,
)


def redact_sensitive_value(value: Any) -> Any:
    if isinstance(value, dict):
        return redact_dict(value)
    if isinstance(value, list):
        return [redact_sensitive_value(item) for item in value]
    if isinstance(value, str) and len(value) > 24:
        if value.startswith("ghp_") or value.startswith("github_pat_"):
            return "[REDACTED_GITHUB_TOKEN]"
        if "Bearer " in value:
            return "[REDACTED_BEARER]"
    return value


def redact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in payload.items():
        if _SENSITIVE_KEY.search(str(key)):
            out[key] = "[REDACTED]"
            continue
        out[key] = redact_sensitive_value(value)
    return out
