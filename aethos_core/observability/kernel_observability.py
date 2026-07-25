# SPDX-License-Identifier: Apache-2.0
"""KERNEL_004 — operational kernel runtime metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.observability.metrics import increment, snapshot_metrics

KERNEL_COUNTER_NAMES: tuple[str, ...] = (
    "kernel_requests_total",
    "kernel_success_total",
    "kernel_recovery_total",
    "kernel_fallback_total",
    "kernel_session_resolved_total",
    "kernel_subject_resolution_failures",
    "kernel_tool_execution_failures",
    "kernel_plan_resume_total",
    "legacy_router_invocations_total",
)


@dataclass
class KernelTurnObservation:
    ok: bool
    intent: str = ""
    used_recovery: bool = False
    used_fallback: bool = False
    subject_resolved: bool = True
    tool_failed: bool = False
    plan_resume: bool = False
    legacy_router: str = ""
    meta: dict[str, str] = field(default_factory=dict)


def record_kernel_turn(obs: KernelTurnObservation) -> None:
    increment("kernel_requests_total")
    if obs.ok:
        increment("kernel_success_total")
    if obs.used_recovery:
        increment("kernel_recovery_total")
    if obs.used_fallback:
        increment("kernel_fallback_total")
    if obs.subject_resolved:
        increment("kernel_session_resolved_total")
    else:
        increment("kernel_subject_resolution_failures")
    if obs.tool_failed:
        increment("kernel_tool_execution_failures")
    if obs.plan_resume:
        increment("kernel_plan_resume_total")
    if obs.legacy_router:
        increment("legacy_router_invocations_total")


def record_legacy_router_invocation(router_id: str) -> None:
    increment("legacy_router_invocations_total")
    increment(f"legacy_router.{router_id}")


def kernel_metrics_snapshot() -> dict[str, Any]:
    snap = snapshot_metrics()
    counters = dict(snap.get("counters") or {})
    kernel_counters = {name: counters.get(name, 0.0) for name in KERNEL_COUNTER_NAMES}
    requests = float(kernel_counters.get("kernel_requests_total") or 0)
    success = float(kernel_counters.get("kernel_success_total") or 0)
    legacy = float(kernel_counters.get("legacy_router_invocations_total") or 0)
    return {
        "kernel_counters": kernel_counters,
        "kernel_success_rate": round(success / requests, 4) if requests else None,
        "legacy_share": round(legacy / (requests + legacy), 4) if (requests + legacy) else None,
        "all_counters": counters,
        "collected_at": snap.get("collected_at"),
    }


def all_kernel_metrics_emitted() -> bool:
    snap = kernel_metrics_snapshot()
    counters = snap.get("kernel_counters") or {}
    return all(name in counters for name in KERNEL_COUNTER_NAMES)
