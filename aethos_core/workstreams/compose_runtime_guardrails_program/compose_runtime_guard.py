# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E4 / FIX 346 — compose runtime guard (shared enforcement layer)."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from aethos_core.workstreams.intelligence_performance_evidence_scalability_program.intelligence_performance_evidence_scalability_program_contract import (
    BASELINE_COMPOSE_TIMINGS_SEC,
)

RUNTIME_MODES: tuple[str, ...] = (
    "lightweight",
    "test",
    "operator",
    "benchmark",
    "full_evidence",
)

MODES_ALLOWING_HEAVY_COMPOSE: frozenset[str] = frozenset({"benchmark", "full_evidence"})

COMPOSE_COST_CLASSIFICATION: dict[str, str] = {
    "FIX 295": "fast",
    "FIX 296": "fast",
    "FIX 301": "fast",
    "FIX 318": "moderate",
    "FIX 314": "slow",
    "FIX 319": "slow",
    "FIX 320": "moderate",
    "FIX 321": "moderate",
    "FIX 322": "critical",
    "FIX 323": "critical",
}

CRITICAL_COMPOSE_MODULES: frozenset[str] = frozenset({"FIX 322", "FIX 323"})
RECURSIVE_FAN_IN_MODULES: frozenset[str] = frozenset({"FIX 322", "FIX 323", "FIX 319"})

RUNTIME_TIMEOUT_POLICY: dict[str, Any] = {
    "warning_threshold_sec": 300.0,
    "soft_timeout_sec": 1800.0,
    "hard_timeout_sec": 7200.0,
    "critical_modules": sorted(CRITICAL_COMPOSE_MODULES),
}

BENCHMARK_COMMANDS: tuple[str, ...] = (
    "run compose benchmark",
    "run full evidence benchmark",
    "run critical compose benchmark",
)

_session_modes: dict[str, str] = {}
_session_approvals: dict[str, set[str]] = {}
_heavy_execution_log: list[dict[str, Any]] = []


class HeavyComposeGuardError(RuntimeError):
    """Raised when a guarded critical compose path is invoked without explicit mode approval."""


@dataclass(frozen=True)
class ComposeGuardDecision:
    allowed: bool
    mode: str
    module: str
    reason: str
    evidence_reduction_performed: bool = False


def clear_compose_runtime_guard_for_tests() -> None:
    _session_modes.clear()
    _session_approvals.clear()
    _heavy_execution_log.clear()


def _normalize_session_id(session_id: str) -> str:
    return (session_id or "default").strip()[:64] or "default"


def _pytest_active() -> bool:
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def get_runtime_mode(*, session_id: str | None = None) -> str:
    sid = _normalize_session_id(session_id or "default")
    if sid in _session_modes:
        return _session_modes[sid]

    env_mode = os.environ.get("AETHOS_COMPOSE_RUNTIME_MODE", "").strip().lower()
    if env_mode in RUNTIME_MODES:
        return env_mode

    if _pytest_active():
        return "test"

    return "operator"


def set_runtime_mode(*, session_id: str, mode: str) -> str:
    normalized = str(mode or "").strip().lower()
    if normalized not in RUNTIME_MODES:
        raise ValueError(f"unsupported runtime mode: {mode!r}")
    sid = _normalize_session_id(session_id)
    _session_modes[sid] = normalized
    return normalized


def grant_heavy_compose_approval(*, session_id: str, module: str) -> None:
    sid = _normalize_session_id(session_id)
    normalized_module = str(module or "").strip().upper()
    _session_approvals.setdefault(sid, set()).add(normalized_module)


def has_heavy_compose_approval(*, session_id: str, module: str) -> bool:
    sid = _normalize_session_id(session_id)
    return str(module or "").strip().upper() in _session_approvals.get(sid, set())


def classify_compose_cost(module: str) -> str:
    return COMPOSE_COST_CLASSIFICATION.get(str(module or "").strip().upper(), "moderate")


def evaluate_heavy_compose_guard(
    *,
    module: str,
    session_id: str,
    lightweight_path: bool = False,
    snapshot_available: bool = False,
) -> ComposeGuardDecision:
    normalized_module = str(module or "").strip().upper()
    mode = get_runtime_mode(session_id=session_id)

    if lightweight_path or snapshot_available or mode == "lightweight":
        return ComposeGuardDecision(
            allowed=True,
            mode=mode,
            module=normalized_module,
            reason="lightweight_or_snapshot_path",
        )

    if normalized_module not in CRITICAL_COMPOSE_MODULES and normalized_module not in RECURSIVE_FAN_IN_MODULES:
        return ComposeGuardDecision(
            allowed=True,
            mode=mode,
            module=normalized_module,
            reason="non_guarded_module",
        )

    if mode in MODES_ALLOWING_HEAVY_COMPOSE:
        return ComposeGuardDecision(
            allowed=True,
            mode=mode,
            module=normalized_module,
            reason="explicit_heavy_compose_mode",
        )

    if has_heavy_compose_approval(session_id=session_id, module=normalized_module):
        return ComposeGuardDecision(
            allowed=True,
            mode=mode,
            module=normalized_module,
            reason="session_heavy_compose_approval",
        )

    return ComposeGuardDecision(
        allowed=False,
        mode=mode,
        module=normalized_module,
        reason="heavy_compose_requires_benchmark_or_full_evidence_mode",
    )


def assert_heavy_compose_allowed(
    *,
    module: str,
    session_id: str,
    lightweight_path: bool = False,
    snapshot_available: bool = False,
) -> ComposeGuardDecision:
    decision = evaluate_heavy_compose_guard(
        module=module,
        session_id=session_id,
        lightweight_path=lightweight_path,
        snapshot_available=snapshot_available,
    )
    if not decision.allowed:
        raise HeavyComposeGuardError(
            f"{decision.module} heavy compose blocked in {decision.mode} mode — "
            "use benchmark/full_evidence mode or an explicit benchmark command"
        )
    return decision


def record_heavy_compose_execution(
    *,
    module: str,
    session_id: str,
    duration_sec: float,
    mode: str,
    guarded: bool,
) -> dict[str, Any]:
    entry = {
        "module": str(module or "").strip().upper(),
        "session_id": _normalize_session_id(session_id),
        "duration_sec": round(float(duration_sec), 3),
        "mode": mode,
        "guarded": guarded,
        "warning": float(duration_sec) >= RUNTIME_TIMEOUT_POLICY["warning_threshold_sec"],
        "recorded_at": time.time(),
        "evidence_reduction_performed": False,
    }
    _heavy_execution_log.append(entry)
    if len(_heavy_execution_log) > 200:
        del _heavy_execution_log[:-200]
    return entry


def list_heavy_compose_executions(*, session_id: str | None = None) -> list[dict[str, Any]]:
    if not session_id:
        return list(_heavy_execution_log)
    sid = _normalize_session_id(session_id)
    return [row for row in _heavy_execution_log if row.get("session_id") == sid]


def build_runtime_mode_registry(*, session_id: str) -> dict[str, Any]:
    mode = get_runtime_mode(session_id=session_id)
    return {
        "registry_id": "runtime-mode-registry",
        "session_id": _normalize_session_id(session_id),
        "active_mode": mode,
        "supported_modes": list(RUNTIME_MODES),
        "modes_allowing_heavy_compose": sorted(MODES_ALLOWING_HEAVY_COMPOSE),
        "pytest_detected": _pytest_active(),
        "read_only": True,
    }


def build_compose_cost_classification_report(*, session_id: str) -> dict[str, Any]:
    _ = session_id
    modules = []
    for module, cost_class in COMPOSE_COST_CLASSIFICATION.items():
        modules.append(
            {
                "module": module,
                "cost_class": cost_class,
                "baseline_duration_sec": BASELINE_COMPOSE_TIMINGS_SEC.get(module),
                "guarded": module in CRITICAL_COMPOSE_MODULES,
            }
        )
    return {
        "report_id": "compose-cost-classification-report",
        "modules": modules,
        "critical_modules": sorted(CRITICAL_COMPOSE_MODULES),
        "read_only": True,
    }


@contextmanager
def runtime_mode_context(*, session_id: str, mode: str) -> Iterator[str]:
    sid = _normalize_session_id(session_id)
    previous = _session_modes.get(sid)
    set_runtime_mode(session_id=sid, mode=mode)
    try:
        yield mode
    finally:
        if previous is None:
            _session_modes.pop(sid, None)
        else:
            _session_modes[sid] = previous


def resolve_benchmark_command(text: str) -> dict[str, Any] | None:
    normalized = str(text or "").strip().lower()
    if normalized == "run compose benchmark":
        return {"command": "run_compose_benchmark", "mode": "benchmark"}
    if normalized == "run full evidence benchmark":
        return {"command": "run_full_evidence_benchmark", "mode": "full_evidence"}
    if normalized == "run critical compose benchmark":
        return {
            "command": "run_critical_compose_benchmark",
            "mode": "benchmark",
            "modules": sorted(CRITICAL_COMPOSE_MODULES),
        }
    return None
