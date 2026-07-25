# SPDX-License-Identifier: Apache-2.0
"""Human-readable formatting for execution artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def normalize_production_url(url: str | None) -> str | None:
    raw = (url or "").strip()
    if not raw:
        return None
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return f"https://{raw.lstrip('/')}"


def truncate_text(text: str | None, *, limit: int = 120) -> str:
    raw = (text or "").strip().replace("\n", " ")
    if len(raw) <= limit:
        return raw
    return raw[: limit - 1].rstrip() + "…"


def format_timestamp(at: Any) -> str | None:
    if at is None or at == "":
        return None
    if isinstance(at, str):
        cleaned = at.strip()
        if cleaned.endswith("Z"):
            try:
                dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
                return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            except ValueError:
                return cleaned
        if cleaned.isdigit():
            at = int(cleaned)
        else:
            return cleaned
    if isinstance(at, (int, float)):
        ts = float(at)
        if ts > 1_000_000_000_000:
            ts /= 1000.0
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except (OSError, OverflowError, ValueError):
            return str(at)
    return str(at)
