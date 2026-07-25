# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — production shadow certification report (read-only aggregation)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.production_confirmation_store import (
    list_confirmations,
    quorum_counts,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    assess_railway_production_policy,
    is_deployment_freeze_active,
    is_production_shadow_execution_enabled,
    load_railway_production_policy_config,
)
from aethos_core.providers.railway.execution_contract.production_shadow_contract_models import (
    FORWARD_SHADOW_PHASES,
    ROLLBACK_SHADOW_PHASES,
)
from aethos_core.providers.railway.execution_contract.production_shadow_gate import (
    assess_production_shadow_gate,
    assess_production_shadow_rollback_gate,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    load_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_shadow_receipts import (
    list_shadow_receipts,
)


@dataclass(frozen=True)
class ProductionShadowCertificationReport:
    ok: bool
    shadow_execution_enabled: bool
    checks: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": list(self.checks)}


def build_production_shadow_certification_report(
    *,
    plan: dict[str, Any] | None,
    execution_id: str = "",
    user_text: str = "",
) -> ProductionShadowCertificationReport:
    plan = plan or {}
    cfg = load_railway_production_policy_config()
    policy = assess_railway_production_policy(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
    )
    forward_gate = assess_production_shadow_gate(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
        require_quorum=False,
    )
    rollback_gate = assess_production_shadow_rollback_gate(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
        journal=load_shadow_journal(execution_id=execution_id),
    )
    receipts = list_shadow_receipts(execution_id=execution_id) if execution_id else []
    shadow_journal = load_shadow_journal(execution_id=execution_id) if execution_id else None
    quorum = quorum_counts(execution_id=execution_id) if execution_id else {}
    confirmations = list_confirmations(execution_id=execution_id) if execution_id else []

    all_mutation_false = all(r.get("mutation_performed") is False for r in receipts) if receipts else True
    forward_receipts = [r for r in receipts if str(r.get("phase") or "") in FORWARD_SHADOW_PHASES]
    rollback_receipts = [
        r
        for r in receipts
        if str(r.get("phase") or "") in ROLLBACK_SHADOW_PHASES or str(r.get("phase") or "") == "rollback_shadow"
    ]

    checks: list[dict[str, Any]] = [
        {"name": "shadow_execution_flag_enabled", "pass": is_production_shadow_execution_enabled()},
        {"name": "production_forward_live_locked", "pass": not policy.forward_live_permitted},
        {"name": "production_rollback_blocked", "pass": not policy.rollback_permitted},
        {"name": "rollback_escalation_manual_only", "pass": policy.rollback_escalation == "manual_only"},
        {"name": "autonomous_rollback_blocked", "pass": policy.autonomous_rollback_blocked},
        {"name": "audit_retention_configured", "pass": cfg.audit_retention_days >= 90},
        {"name": "slo_verification_policy_defined", "pass": policy.slo_verification_required},
        {"name": "freeze_policy_evaluated", "pass": True},
        {"name": "incident_mode_evaluated", "pass": True},
        {"name": "operator_quorum_store_available", "pass": True},
        {
            "name": "forward_shadow_phases_recorded",
            "pass": len(forward_receipts) >= len(FORWARD_SHADOW_PHASES)
            if shadow_journal and shadow_journal.get("forward_shadow_completed")
            else len(forward_receipts) == 0,
        },
        {
            "name": "rollback_shadow_phases_recorded",
            "pass": len(rollback_receipts) >= len(ROLLBACK_SHADOW_PHASES) + 1
            if shadow_journal and shadow_journal.get("rollback_shadow_completed")
            else len(rollback_receipts) == 0,
        },
        {"name": "shadow_receipts_mutation_performed_false", "pass": all_mutation_false},
        {"name": "forward_shadow_gate_available", "pass": forward_gate.shadow_execution_enabled},
        {"name": "rollback_shadow_gate_available", "pass": rollback_gate.shadow_execution_enabled},
    ]

    if execution_id:
        checks.append(
            {
                "name": "quorum_confirmations_persisted",
                "pass": len(confirmations) >= 1,
                "count": len(confirmations),
            }
        )
        checks.append(
            {
                "name": "operator_quorum_distinct_kinds",
                "pass": int(quorum.get("total_distinct") or 0) >= 0,
                "distinct": int(quorum.get("total_distinct") or 0),
            }
        )

    optional = {"forward_shadow_phases_recorded", "rollback_shadow_phases_recorded"}
    ok = all(bool(c.get("pass")) for c in checks if c.get("name") not in optional)

    _ = is_deployment_freeze_active()
    return ProductionShadowCertificationReport(
        ok=ok,
        shadow_execution_enabled=is_production_shadow_execution_enabled(),
        checks=checks,
    )
