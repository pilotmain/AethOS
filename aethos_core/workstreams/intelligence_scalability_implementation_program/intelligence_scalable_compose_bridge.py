# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E3 / FIX 345 — scalable compose bridge for FIX 322/323 evidence paths."""

from __future__ import annotations

from typing import Any, Callable

from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_compose_cache import (
    get_artifact_snapshot,
    get_or_memoize_module,
    store_artifact_snapshot,
)
from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_contract import (
    MEMOIZATION_MODULES,
    PMF_SNAPSHOT_MODULE,
    VALUE_SNAPSHOT_MODULE,
)

_MODULE_KEY_MAP: dict[str, str] = {
    "fix_295": "FIX 295",
    "fix_296": "FIX 296",
    "fix_301": "FIX 301",
    "fix_322": PMF_SNAPSHOT_MODULE,
    "fix_323": VALUE_SNAPSHOT_MODULE,
}

_active_sessions: set[str] = set()


def enable_scalable_compose(*, session_id: str) -> None:
    sid = (session_id or "default").strip()[:64] or "default"
    _active_sessions.add(sid)


def disable_scalable_compose(*, session_id: str) -> None:
    sid = (session_id or "default").strip()[:64] or "default"
    _active_sessions.discard(sid)


def clear_scalable_compose_sessions_for_tests() -> None:
    _active_sessions.clear()


def is_scalable_compose_enabled(*, session_id: str) -> bool:
    sid = (session_id or "default").strip()[:64] or "default"
    if sid in _active_sessions:
        return True
    return __import__("os").environ.get("AETHOS_SCALABLE_COMPOSE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def _payload(result: Any, attr: str) -> dict[str, Any]:
    if not result:
        return {}
    board = getattr(result, attr, None)
    return board if isinstance(board, dict) else {}


def memoized_compose_build(
    *,
    session_id: str,
    module_key: str,
    attr: str,
    builder: Callable[..., Any],
) -> tuple[dict[str, Any], bool]:
    fix_label = _MODULE_KEY_MAP.get(module_key, module_key.upper().replace("_", " "))
    if fix_label not in MEMOIZATION_MODULES or not is_scalable_compose_enabled(session_id=session_id):
        try:
            result = builder(session_id=session_id)
            return _payload(result, attr), bool(getattr(result, "ok", True))
        except Exception:
            return {}, False

    def _build_payload() -> dict[str, Any]:
        result = builder(session_id=session_id)
        return {
            "payload": _payload(result, attr),
            "ok": bool(getattr(result, "ok", True)),
            "truth_mutation_performed": False,
        }

    cached = get_or_memoize_module(session_id=session_id, module=fix_label, builder=_build_payload)
    inner = cached.get("payload") or {}
    if isinstance(inner, dict) and "payload" in inner and "ok" in inner:
        return inner.get("payload") or {}, bool(inner.get("ok"))
    return inner if isinstance(inner, dict) else {}, True


def load_pmf_snapshot(*, session_id: str) -> dict[str, Any] | None:
    if not is_scalable_compose_enabled(session_id=session_id):
        return None
    entry = get_artifact_snapshot(session_id=session_id, module=PMF_SNAPSHOT_MODULE)
    if not entry:
        return None
    artifact = entry.get("artifact") or {}
    return artifact.get("board") if isinstance(artifact.get("board"), dict) else artifact


def record_pmf_snapshot(*, session_id: str, board: dict[str, Any]) -> dict[str, Any]:
    return store_artifact_snapshot(
        session_id=session_id,
        module=PMF_SNAPSHOT_MODULE,
        artifact={
            "board": board,
            "module": PMF_SNAPSHOT_MODULE,
            "truth_mutation_performed": False,
            "evidence_provenance_preserved": True,
        },
    )


def record_value_realization_snapshot(*, session_id: str, board: dict[str, Any]) -> dict[str, Any]:
    return store_artifact_snapshot(
        session_id=session_id,
        module=VALUE_SNAPSHOT_MODULE,
        artifact={
            "board": board,
            "module": VALUE_SNAPSHOT_MODULE,
            "truth_mutation_performed": False,
            "evidence_provenance_preserved": True,
        },
    )


def load_value_realization_snapshot(*, session_id: str) -> dict[str, Any] | None:
    if not is_scalable_compose_enabled(session_id=session_id):
        return None
    entry = get_artifact_snapshot(session_id=session_id, module=VALUE_SNAPSHOT_MODULE)
    if not entry:
        return None
    artifact = entry.get("artifact") or {}
    return artifact.get("board") if isinstance(artifact.get("board"), dict) else artifact
