# SPDX-License-Identifier: Apache-2.0
"""Capability registry — providers expose capabilities, not handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

CapabilityScope = Literal[
    "provider_service",
    "provider_wide",
    "failed_service",
    "active_target",
    "formatting",
    "internal",
    "any",
]


@dataclass(frozen=True)
class Capability:
    name: str
    provider: str
    readonly: bool
    supports: tuple[CapabilityScope, ...]
    description: str = ""
    handler_ref: str = ""


_REGISTRY: dict[str, Capability] = {}


def register_capability(cap: Capability) -> None:
    _REGISTRY[cap.name] = cap


def get_capability(name: str) -> Capability | None:
    return _REGISTRY.get(name)


def list_capabilities(*, provider: str | None = None, readonly: bool | None = None) -> list[Capability]:
    rows = list(_REGISTRY.values())
    if provider:
        rows = [row for row in rows if row.provider == provider or row.provider == "aethos"]
    if readonly is not None:
        rows = [row for row in rows if row.readonly == readonly]
    return rows


def _bootstrap_registry() -> None:
    if _REGISTRY:
        return
    defaults = [
        Capability("fetch_runtime_logs", "railway", True, ("provider_service", "failed_service", "active_target"), "Fetch deployment/runtime logs", "failed_service_diagnosis.fetch_railway_logs_multisource"),
        Capability("fetch_service_events", "railway", True, ("provider_service", "failed_service"), "Fetch Railway service/deployment events", "service_events_api.get_service_events"),
        Capability("classify_failure", "railway", True, ("failed_service",), "Classify root cause from evidence", "root_cause_classifier.classify_root_cause"),
        Capability("compose_diagnosis", "aethos", True, ("failed_service",), "Compose bounded diagnosis reply", "failed_service_diagnosis.compose_diagnosis_reply"),
        Capability("compose_fix_plan", "aethos", True, ("failed_service",), "Compose governed fix plan", "failed_service_fix_plan.compose_fix_plan_reply"),
        Capability("provider_wide_health", "railway", True, ("provider_wide",), "Collect provider-wide health inventory", "railway_wide_health.compose_railway_provider_wide_health_reply"),
        Capability("transform_response", "aethos", True, ("formatting",), "Semantic rerender/filter/format", "response_composer.try_compose_rerender_reply"),
        Capability("inspect_route_trace", "aethos", True, ("internal",), "Return internal route trace metadata", "route_trace.compose_internal_route_trace_reply"),
        Capability("verify_restart", "railway", True, ("active_target",), "Verify restart/deployment transition", "railway_adapter.verify_restart"),
        Capability("fetch_health", "railway", True, ("provider_service", "provider_wide", "active_target"), "Fetch service health state", "railway_wide_health.collect_railway_service_health_rows"),
        Capability("discover_provider_inventory", "railway", True, ("provider_wide", "failed_service"), "Discover provider topology when cache missing", "fallback_discovery.discover_provider_if_cache_missing"),
        Capability("collect_health_state", "railway", True, ("provider_wide", "failed_service"), "Refresh provider-wide health cache", "fallback_discovery.refresh_health_report_if_needed"),
        Capability("resolve_target", "aethos", True, ("failed_service",), "Resolve failed-service target with fallback discovery", "fallback_discovery.resolve_failed_service_with_fallback"),
        Capability("correlate_evidence_freshness", "aethos", True, ("failed_service",), "Correlate evidence freshness and conflicts", "correlated_diagnosis.correlate_evidence"),
        Capability("plan_best_next_step", "aethos", True, ("failed_service",), "Plan single best next operational step", "next_step_planner.plan_best_next_step"),
    ]
    for cap in defaults:
        register_capability(cap)


def ensure_registry() -> None:
    _bootstrap_registry()
