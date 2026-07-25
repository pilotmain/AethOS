# SPDX-License-Identifier: Apache-2.0
"""Capability planner — dynamic capability chains from cognition decisions."""

from __future__ import annotations

from aethos_core.capabilities.capability_registry import ensure_registry
from aethos_core.operational_cognition.types import OperationalCognitionDecision


def plan_capability_chain(decision: OperationalCognitionDecision, *, session_id: str = "default") -> list[str]:
    ensure_registry()
    intent = decision.intent
    fallback_prefix = _fallback_capabilities_for(intent, session_id=session_id)

    if intent == "inspect_route_trace":
        return ["inspect_route_trace"]
    if intent == "transform_response":
        return ["transform_response"]
    if intent in {"inventory_health_report", "inventory_list"}:
        return ["fetch_health", "provider_wide_health"]
    if intent == "fetch_events":
        return fallback_prefix + ["fetch_service_events", "classify_failure", "compose_diagnosis"]
    if intent == "fetch_logs":
        return fallback_prefix + ["fetch_runtime_logs", "compose_diagnosis"]
    if intent == "create_fix_plan":
        return fallback_prefix + ["fetch_runtime_logs", "fetch_service_events", "classify_failure", "compose_fix_plan"]
    if intent == "diagnose_failure":
        return fallback_prefix + ["fetch_runtime_logs", "fetch_service_events", "classify_failure", "compose_diagnosis"]
    if intent in {"verify_operation", "health_check"}:
        return ["verify_restart", "fetch_runtime_logs"]
    if intent == "mutation":
        return []
    return chain if (chain := fallback_prefix) else []


def attach_capabilities(decision: OperationalCognitionDecision, *, session_id: str = "default") -> OperationalCognitionDecision:
    decision.capabilities = plan_capability_chain(decision, session_id=session_id)
    return decision


def _fallback_capabilities_for(intent: str, *, session_id: str) -> list[str]:
    if intent not in {"diagnose_failure", "create_fix_plan", "fetch_logs", "fetch_events"}:
        return []
    from aethos_core.failed_service_investigation.fallback_discovery import cache_has_health_report

    prefix: list[str] = []
    if not cache_has_health_report(session_id=session_id, provider="railway"):
        prefix = ["discover_provider_inventory", "resolve_target", "collect_health_state"]
    if intent in {"diagnose_failure", "create_fix_plan", "fetch_logs", "fetch_events"}:
        prefix.extend(["correlate_evidence_freshness", "plan_best_next_step"])
    return prefix
