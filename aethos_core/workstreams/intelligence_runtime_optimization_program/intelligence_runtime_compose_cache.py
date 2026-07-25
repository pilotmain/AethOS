# SPDX-License-Identifier: Apache-2.0
"""FIX 344 / WORKSTREAM_E2 — session-scoped intelligence compose cache."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_DEFAULT_CACHE = Path("data/workstream_e2_intelligence_runtime/compose_cache.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _cache_path() -> Path:
    return Path(
        __import__("os").environ.get(
            "AETHOS_WORKSTREAM_E2_COMPOSE_CACHE",
            str(_DEFAULT_CACHE),
        )
    )


def _load_raw() -> dict[str, Any]:
    empty: dict[str, Any] = {
        "memoized_modules": {},
        "artifact_snapshots": {},
        "metrics": {
            "cache_hits": 0,
            "cache_misses": 0,
            "artifact_reuse_count": 0,
            "artifact_store_count": 0,
        },
    }
    path = _cache_path()
    if not path.exists():
        return empty
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty
    if not isinstance(payload, dict):
        return empty
    for key in empty:
        if key == "metrics":
            if not isinstance(payload.get("metrics"), dict):
                payload["metrics"] = dict(empty["metrics"])
        elif not isinstance(payload.get(key), dict):
            payload[key] = {}
    return payload


def _save_raw(payload: dict[str, Any]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def clear_intelligence_runtime_compose_cache_for_tests() -> None:
    path = _cache_path()
    if path.exists():
        path.unlink(missing_ok=True)


def _session_key(session_id: str, module: str) -> str:
    sid = (session_id or "default").strip()[:64] or "default"
    return f"{sid}::{module}"


def get_compose_cache_metrics() -> dict[str, Any]:
    metrics = dict(_load_raw().get("metrics") or {})
    hits = int(metrics.get("cache_hits") or 0)
    misses = int(metrics.get("cache_misses") or 0)
    total = hits + misses
    metrics["cache_hit_ratio"] = round(hits / total, 4) if total else 0.0
    stores = int(metrics.get("artifact_store_count") or 0)
    reuses = int(metrics.get("artifact_reuse_count") or 0)
    metrics["artifact_reuse_ratio"] = round(reuses / stores, 4) if stores else 0.0
    return metrics


def get_or_memoize_module(
    *,
    session_id: str,
    module: str,
    builder: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    payload = _load_raw()
    key = _session_key(session_id, module)
    memoized = payload.get("memoized_modules") or {}
    metrics = dict(payload.get("metrics") or {})

    if key in memoized:
        metrics["cache_hits"] = int(metrics.get("cache_hits") or 0) + 1
        payload["metrics"] = metrics
        _save_raw(payload)
        cached = dict(memoized[key])
        cached["cache_hit"] = True
        return cached

    result = builder()
    metrics["cache_misses"] = int(metrics.get("cache_misses") or 0) + 1
    entry = {
        "module": module,
        "session_id": session_id,
        "payload": result,
        "cached_at": _utc_now(),
        "truth_reduction_performed": False,
    }
    memoized[key] = entry
    payload["memoized_modules"] = memoized
    payload["metrics"] = metrics
    _save_raw(payload)
    return {**entry, "cache_hit": False}


def store_artifact_snapshot(
    *,
    session_id: str,
    module: str,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    payload = _load_raw()
    key = _session_key(session_id, module)
    snapshots = payload.get("artifact_snapshots") or {}
    metrics = dict(payload.get("metrics") or {})
    entry = {
        "module": module,
        "session_id": session_id,
        "artifact": artifact,
        "stored_at": _utc_now(),
        "truth_reduction_performed": False,
    }
    snapshots[key] = entry
    metrics["artifact_store_count"] = int(metrics.get("artifact_store_count") or 0) + 1
    payload["artifact_snapshots"] = snapshots
    payload["metrics"] = metrics
    _save_raw(payload)
    return entry


def get_artifact_snapshot(*, session_id: str, module: str) -> dict[str, Any] | None:
    payload = _load_raw()
    key = _session_key(session_id, module)
    snapshots = payload.get("artifact_snapshots") or {}
    entry = snapshots.get(key)
    if not entry:
        return None
    metrics = dict(payload.get("metrics") or {})
    metrics["artifact_reuse_count"] = int(metrics.get("artifact_reuse_count") or 0) + 1
    payload["metrics"] = metrics
    _save_raw(payload)
    return dict(entry)
