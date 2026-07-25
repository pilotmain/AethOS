# SPDX-License-Identifier: Apache-2.0
"""Redact secrets from logs, UI copy, and artifacts."""

from __future__ import annotations

import re
from typing import Any

_TOKEN_PATTERNS = (
    re.compile(r"\b(vercel_[a-zA-Z0-9_]{20,})\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-+/=]{20,}\b", re.I),
    re.compile(r"\b(api[_-]?token|password|secret|authorization)\s*[:=]\s*\S+\b", re.I),
    # Well-known API-key prefixes (provider tokens that may surface in tool
    # results / progress narration). Strictly additive — only ever masks more.
    re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"),          # Anthropic
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),                  # OpenAI-style
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),           # GitHub
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),         # Slack
    re.compile(r"\bre_[A-Za-z0-9_]{20,}\b"),                 # Resend
)

# §10 PII patterns — applied to logs (not general content) when enabled.
_PII_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),          # email
    re.compile(r"\b(?:\+?\d[\s.\-]?){7,}\d\b"),                                    # phone-ish
    re.compile(r"\b(?:\d[ \-]?){13,16}\b"),                                        # card-ish
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),                                          # US SSN
)


def mask_secret(value: str, *, visible: int = 4) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    if len(raw) <= visible * 2:
        return "*" * len(raw)
    return f"{raw[:visible]}{'*' * max(4, len(raw) - visible * 2)}{raw[-visible:]}"


def redact_text(text: str) -> str:
    out = text or ""
    for pattern in _TOKEN_PATTERNS:
        out = pattern.sub(lambda m: mask_secret(m.group(0)), out)
    return out


def redact_value(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {k: redact_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(v) for v in value]
    return value


def redact_pii(text: str) -> str:
    """Mask common PII (email, phone, card, SSN). For log sinks (§10)."""
    out = text or ""
    for pattern in _PII_PATTERNS:
        out = pattern.sub(lambda m: mask_secret(m.group(0)), out)
    return out


def redact_known_secrets(text: str, secrets: Any) -> str:
    """Mask exact occurrences of known secret values, then apply pattern redaction.

    Used for credentialed execution: any injected token that leaks into CLI/API
    stdout/stderr is masked before the output is returned to the model or logged.
    """
    out = text or ""
    for secret in secrets or []:
        s = str(secret or "").strip()
        if len(s) >= 6:
            out = out.replace(s, mask_secret(s))
    return redact_text(out)


_DOTENV_LINE_RX = re.compile(r"^(\s*(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*\s*=)(.*)$")


def redact_dotenv_values(text: str) -> str:
    """Mask the value side of every ``KEY=VALUE`` line in dotenv-style content.

    Used when the read-only repo tools return the contents of a ``.env`` file —
    keys stay visible (useful for review) but secret values never reach the model
    or chat. Comments and blank lines are preserved.
    """
    out_lines: list[str] = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out_lines.append(line)
            continue
        match = _DOTENV_LINE_RX.match(line)
        if match:
            value = match.group(2).strip()
            if value and value not in ('""', "''"):
                out_lines.append(f"{match.group(1)}***redacted***")
                continue
        out_lines.append(line)
    return "\n".join(out_lines)


def safe_log_message(message: str) -> str:
    return redact_text(message)
