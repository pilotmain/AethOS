# SPDX-License-Identifier: Apache-2.0
"""Operational query planning — intent, scope, provider, target, action."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.operational_planner.action_policy import resolve_action_type
from aethos_core.operational_planner.intent_classifier import classify_operational_intent
from aethos_core.operational_planner.provider_selector import select_provider
from aethos_core.operational_planner.scope_classifier import classify_operational_scope
from aethos_core.operational_planner.target_selector import select_target


@dataclass
class OperationalQueryPlan:
    user_text: str
    scope: str
    intent: str
    provider: str | None
    target: str | None
    action_type: str
    evidence_needed: list[str] = field(default_factory=list)
    overrides_active_thread: bool = False
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_text": self.user_text,
            "scope": self.scope,
            "intent": self.intent,
            "provider": self.provider,
            "target": self.target,
            "action_type": self.action_type,
            "evidence_needed": list(self.evidence_needed),
            "overrides_active_thread": self.overrides_active_thread,
            "meta": dict(self.meta),
        }


def plan_operational_query(text: str, *, session_id: str = "default") -> OperationalQueryPlan:
    raw = (text or "").strip()
    scope = classify_operational_scope(raw, session_id=session_id)
    intent = classify_operational_intent(raw, scope=scope, session_id=session_id)
    provider = select_provider(raw, session_id=session_id, scope=scope)
    target = select_target(raw, session_id=session_id, scope=scope)
    action_type = resolve_action_type(scope=scope, intent=intent)

    evidence_needed: list[str] = []
    if intent == "inventory_health_report":
        evidence_needed = ["service_inventory", "deployment_status", "runtime_health", "recent_errors"]
    elif intent == "health_check":
        evidence_needed = ["service_health", "restart_verification", "latest_logs"]

    overrides = scope in {"provider_wide", "all_providers", "workspace_wide"}

    return OperationalQueryPlan(
        user_text=raw,
        scope=scope,
        intent=intent,
        provider=provider,
        target=target,
        action_type=action_type,
        evidence_needed=evidence_needed,
        overrides_active_thread=overrides,
        meta={"session_id": session_id},
    )
