# SPDX-License-Identifier: Apache-2.0
"""Last-known Railway provider-wide health snapshot for rate-limit resilience."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_RATE_LIMIT_RX = re.compile(
    r"\b(rate\s*limit|too\s+many\s+requests|429)\b",
    re.I,
)
_RETRY_SECONDS_RX = re.compile(r"try\s+again\s+in\s+([\d.]+)\s*seconds", re.I)


def is_rate_limit_error(message: str | None) -> bool:
    return bool(message and _RATE_LIMIT_RX.search(str(message)))


def parse_rate_limit_retry_seconds(message: str | None) -> int | None:
    if not message:
        return None
    match = _RETRY_SECONDS_RX.search(str(message))
    if not match:
        return None
    try:
        return int(float(match.group(1)))
    except ValueError:
        return None


def _cache_path() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_provider_wide_health"
    root.mkdir(parents=True, exist_ok=True)
    return root / "last_known_snapshot.json"


def save_cached_railway_health_rows(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    payload = {
        "rows": list(rows),
        "cached_at": datetime.now(UTC).isoformat(),
        "source": "live_inventory",
    }
    try:
        _cache_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def load_cached_railway_health_rows() -> tuple[list[dict[str, Any]], str | None]:
    path = _cache_path()
    if not path.is_file():
        return [], None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], None
    if not isinstance(raw, dict):
        return [], None
    rows = raw.get("rows")
    if not isinstance(rows, list) or not rows:
        return [], None
    cached_at = str(raw.get("cached_at") or "")
    return [dict(row) for row in rows if isinstance(row, dict)], cached_at or None


def clear_cache_for_tests() -> None:
    try:
        _cache_path().unlink(missing_ok=True)
    except OSError:
        pass
