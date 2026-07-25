# SPDX-License-Identifier: Apache-2.0
"""Secret handling for mutation governance — never log raw values."""

from __future__ import annotations

import hashlib
import re
from typing import Any


_ENV_SET_RX = re.compile(
    r"\bset\b.*\b(?:env(?:ironment)?\s+var(?:iable)?|variable)\s+([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)",
    re.I,
)


def masked_secret_reference(*, name: str, value: str | None = None) -> dict[str, Any]:
    raw = (value or "").strip()
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12] if raw else None
    return {
        "kind": "masked_secret_reference",
        "name": name,
        "value_present": bool(raw),
        "value_digest": digest,
        "masked_value": "***" if raw else None,
    }


def parse_env_var_from_request(user_request: str) -> dict[str, Any] | None:
    m = _ENV_SET_RX.search(user_request or "")
    if not m:
        return None
    name = m.group(1)
    value = m.group(2).strip().strip("'\"")
    return {
        "env_var_name": name,
        "env_var_reference": masked_secret_reference(name=name, value=value),
    }


def redact_secrets_in_text(text: str) -> str:
    return re.sub(
        r"(\b[A-Za-z_][A-Za-z0-9_]*=)([^\s]+)",
        r"\1***",
        text or "",
    )
