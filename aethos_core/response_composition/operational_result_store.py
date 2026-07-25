# SPDX-License-Identifier: Apache-2.0
"""Persist structured operational results for semantic re-rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_PROVIDER_WIDE_TTL = timedelta(hours=2)
_THREAD_TTL = timedelta(hours=8)

_MEMORY: dict[str, dict[str, Any]] = {}


@dataclass
class OperationalResult:
    operation_type: str
    provider: str
    scope: str
    result_payload: dict[str, Any]
    result_timestamp: str
    summary: dict[str, Any] = field(default_factory=dict)
    filters: dict[str, Any] = field(default_factory=dict)
    render_history: list[dict[str, str]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_type": self.operation_type,
            "provider": self.provider,
            "scope": self.scope,
            "result_payload": dict(self.result_payload),
            "result_timestamp": self.result_timestamp,
            "summary": dict(self.summary),
            "filters": dict(self.filters),
            "render_history": list(self.render_history),
            "meta": dict(self.meta),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> OperationalResult:
        return cls(
            operation_type=str(raw.get("operation_type") or ""),
            provider=str(raw.get("provider") or ""),
            scope=str(raw.get("scope") or ""),
            result_payload=dict(raw.get("result_payload") or {}),
            result_timestamp=str(raw.get("result_timestamp") or ""),
            summary=dict(raw.get("summary") or {}),
            filters=dict(raw.get("filters") or {}),
            render_history=list(raw.get("render_history") or []),
            meta=dict(raw.get("meta") or {}),
        )


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "response_composition"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_operational_result.json"


def _ttl_for_scope(scope: str) -> timedelta:
    if scope in {"provider_wide", "all_providers", "workspace_wide"}:
        return _PROVIDER_WIDE_TTL
    return _THREAD_TTL


def _is_expired(result: OperationalResult) -> bool:
    try:
        ts = datetime.fromisoformat(result.result_timestamp.replace("Z", "+00:00"))
    except ValueError:
        return True
    return datetime.now(UTC) - ts > _ttl_for_scope(result.scope)


def save_operational_result(*, session_id: str, result: OperationalResult) -> OperationalResult:
    session_id = (session_id or "default").strip()
    payload = result.to_dict()
    _MEMORY[session_id] = payload
    _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return result


def get_latest_operational_result(*, session_id: str) -> OperationalResult | None:
    session_id = (session_id or "default").strip()
    cached = _MEMORY.get(session_id)
    if cached is None:
        path = _session_path(session_id)
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    cached = raw
                    _MEMORY[session_id] = raw
            except (OSError, json.JSONDecodeError):
                return None
    if not cached:
        return None
    result = OperationalResult.from_dict(cached)
    if _is_expired(result):
        return None
    return result


def find_latest_provider_wide_health(*, session_id: str, provider: str = "railway") -> OperationalResult | None:
    """Resolve provider-wide health for a session, with channel-scoped fallback."""
    session_id = (session_id or "default").strip()

    direct = get_latest_operational_result(session_id=session_id)
    if (
        direct is not None
        and direct.operation_type == "provider_wide_health"
        and str(direct.provider or "") == provider
    ):
        return direct

    candidates: list[OperationalResult] = []
    seen_sessions: set[str] = set()

    def _consider(sid: str) -> None:
        sid = (sid or "").strip()
        if not sid or sid in seen_sessions:
            return
        seen_sessions.add(sid)
        result = get_latest_operational_result(session_id=sid)
        if (
            result is not None
            and result.operation_type == "provider_wide_health"
            and str(result.provider or "") == provider
        ):
            candidates.append(result)

    _consider(session_id)
    if session_id.startswith("tg-"):
        chat_prefix = "-".join(session_id.split("-")[:2])
        if chat_prefix:
            for sid in list(_MEMORY.keys()):
                if sid.startswith(chat_prefix):
                    _consider(sid)
            root = _store_dir()
            for path in root.glob(f"{chat_prefix.replace('/', '_')}*_operational_result.json"):
                safe = path.stem.replace("_operational_result", "")
                _consider(safe)

    for sid in list(_MEMORY.keys()):
        _consider(sid)

    root = _store_dir()
    for path in root.glob("*_operational_result.json"):
        safe = path.stem.replace("_operational_result", "")
        _consider(safe)

    if not candidates:
        return None

    candidates.sort(key=lambda row: row.result_timestamp, reverse=True)
    return candidates[0]


def record_render_history(
    *,
    session_id: str,
    output_format: str,
    filter_mode: str = "all",
) -> None:
    result = get_latest_operational_result(session_id=session_id)
    if result is None:
        return
    result.render_history.append(
        {
            "output_format": output_format,
            "filter_mode": filter_mode,
            "rendered_at": datetime.now(UTC).isoformat(),
        }
    )
    save_operational_result(session_id=session_id, result=result)


def clear_operational_results_for_tests() -> None:
    _MEMORY.clear()
    root = _store_dir()
    for path in root.glob("*_operational_result.json"):
        path.unlink(missing_ok=True)
