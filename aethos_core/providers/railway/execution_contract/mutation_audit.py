# SPDX-License-Identifier: Apache-2.0
"""FIX 108B — Live mutation audit report (read-only validation layer)."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_enablement import (
    assess_railway_execution_enablement_policy,
    load_railway_execution_enablement_config,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    MUTATION_RECEIPT_STATUSES,
    SIMULATED_RECEIPT_STATUSES,
    normalize_receipt_status,
    phase_mutation_recorded,
    receipt_is_live_mutation,
    receipt_is_simulated,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    list_execution_receipts,
)
from aethos_core.providers.railway.execution_contract.mutation_preview import (
    assess_railway_mutation_preview,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
    is_railway_mutation_kill_switch_active,
)
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    COMMIT_SKIP_DEPLOYS_ENFORCED,
)


@dataclass
class MutationIsolationCheck:
    name: str
    passed: bool
    detail: str


@dataclass
class RailwayMutationAuditReport:
    ok: bool
    kill_switch_active: bool
    execution_mode: str
    dry_run_cannot_reach_live_adapter: bool
    live_adapter_requires_enabled_mode: bool
    live_adapter_requires_authorization_token: bool
    isolation_checks: list[MutationIsolationCheck] = field(default_factory=list)
    receipt_summary: dict[str, int] = field(default_factory=dict)
    live_mutation_receipt_count: int = 0
    simulated_receipt_count: int = 0
    create_service_mutation_recorded: bool = False
    idempotent_replay_would_skip: bool = False
    preview_would_mutate: bool = False
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "kill_switch_active": self.kill_switch_active,
            "execution_mode": self.execution_mode,
            "dry_run_cannot_reach_live_adapter": self.dry_run_cannot_reach_live_adapter,
            "live_adapter_requires_enabled_mode": self.live_adapter_requires_enabled_mode,
            "live_adapter_requires_authorization_token": self.live_adapter_requires_authorization_token,
            "isolation_checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail} for c in self.isolation_checks
            ],
            "receipt_summary": dict(self.receipt_summary),
            "live_mutation_receipt_count": self.live_mutation_receipt_count,
            "simulated_receipt_count": self.simulated_receipt_count,
            "create_service_mutation_recorded": self.create_service_mutation_recorded,
            "idempotent_replay_would_skip": self.idempotent_replay_would_skip,
            "preview_would_mutate": self.preview_would_mutate,
            "blockers": list(self.blockers),
        }


def _module_source_path(module_name: str) -> Path | None:
    spec = importlib.util.find_spec(module_name)
    if spec is None or not spec.origin:
        return None
    return Path(spec.origin)


def _source_excludes_import(source_path: Path, import_needle: str) -> bool:
    try:
        source = source_path.read_text(encoding="utf-8")
    except OSError:
        return False
    return import_needle not in source


def build_railway_mutation_audit_report(
    *,
    plan: dict[str, Any] | None = None,
    user_text: str = "",
    execution_id: str = "",
    journal: dict[str, Any] | None = None,
) -> RailwayMutationAuditReport:
    cfg = load_railway_execution_enablement_config()
    kill_switch = is_railway_mutation_kill_switch_active()
    policy = assess_railway_execution_enablement_policy(plan=plan or {}, user_text=user_text)
    preview = assess_railway_mutation_preview(
        plan=plan,
        user_text=user_text,
        execution_id=execution_id,
        journal=journal,
    )

    checks: list[MutationIsolationCheck] = []

    dry_run_path = _module_source_path(
        "aethos_core.providers.railway.execution_contract.execution_dry_run_executor"
    )
    dry_run_excludes_adapter = bool(
        dry_run_path
        and _source_excludes_import(dry_run_path, "create_service_adapter")
        and _source_excludes_import(dry_run_path, "create_railway_service")
        and _source_excludes_import(dry_run_path, "connect_github_source")
    )
    checks.append(
        MutationIsolationCheck(
            name="dry_run_executor_does_not_import_live_adapter",
            passed=dry_run_excludes_adapter,
            detail=(
                "execution_dry_run_executor has no import of create_railway_service"
                if dry_run_excludes_adapter
                else "unexpected import of live adapter in dry-run executor"
            ),
        )
    )

    sim_path = _module_source_path(
        "aethos_core.providers.railway.service_creation_simulator.simulator_checks"
    )
    sim_excludes = bool(
        sim_path
        and _source_excludes_import(sim_path, "create_railway_service")
        and _source_excludes_import(sim_path, "connect_github_source")
    )
    checks.append(
        MutationIsolationCheck(
            name="simulator_does_not_import_live_adapter",
            passed=sim_excludes,
            detail="simulator path does not import create_railway_service" if sim_excludes else "check failed",
        )
    )

    create_adapter_path = _module_source_path(
        "aethos_core.providers.railway.greenfield_adapters.create_service_adapter"
    )
    connect_adapter_path = _module_source_path(
        "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter"
    )
    create_gate = bool(
        create_adapter_path
        and "require_live_create_service_authorization"
        in create_adapter_path.read_text(encoding="utf-8")
    )
    connect_gate = bool(
        connect_adapter_path
        and "require_live_connect_github_source_authorization"
        in connect_adapter_path.read_text(encoding="utf-8")
    )
    checks.append(
        MutationIsolationCheck(
            name="live_create_service_adapter_requires_authorization_gate",
            passed=create_gate,
            detail="create_railway_service calls require_live_create_service_authorization()",
        )
    )
    checks.append(
        MutationIsolationCheck(
            name="live_connect_source_adapter_requires_authorization_gate",
            passed=connect_gate,
            detail="connect_github_source calls require_live_connect_github_source_authorization()",
        )
    )
    adapter_has_gate = create_gate and connect_gate

    receipt_summary: dict[str, int] = {}
    live_count = 0
    simulated_count = 0
    create_service_recorded = False
    connect_source_recorded = False
    if execution_id:
        for receipt in list_execution_receipts(execution_id=execution_id):
            normalized = normalize_receipt_status(dict(receipt))
            status = str(normalized.get("status") or "unknown")
            receipt_summary[status] = receipt_summary.get(status, 0) + 1
            if receipt_is_live_mutation(normalized):
                live_count += 1
            if receipt_is_simulated(normalized):
                simulated_count += 1
            phase = str(normalized.get("phase") or "")
            if phase == "create_service" and phase_mutation_recorded(normalized):
                create_service_recorded = True
            if phase == "connect_source" and phase_mutation_recorded(normalized):
                connect_source_recorded = True

    from aethos_core.providers.railway.execution_contract.source_binding_audit import (
        audit_connect_source_receipt,
    )

    connect_receipt_audit = (
        audit_connect_source_receipt(execution_id=execution_id) if execution_id else None
    )
    if connect_receipt_audit and connect_receipt_audit.receipt_found and not connect_receipt_audit.ok:
        checks.append(
            MutationIsolationCheck(
                name="connect_source_receipt_audit",
                passed=False,
                detail="; ".join(connect_receipt_audit.errors) or "connect_source receipt audit failed",
            )
        )
    elif connect_receipt_audit and connect_receipt_audit.receipt_found:
        checks.append(
            MutationIsolationCheck(
                name="connect_source_receipt_audit",
                passed=True,
                detail="connect_source receipt is live mutation with skipDeploys semantics",
            )
        )

    isolation_ok = all(c.passed for c in checks)
    blockers: list[str] = []
    if kill_switch:
        blockers.append("mutation_kill_switch_active")
    if cfg.mode != "enabled":
        blockers.append("execution_mode_not_enabled")

    skip_deploys_check = bool(
        _module_source_path("aethos_core.providers.railway.greenfield_adapters.source_bind_graphql")
        and COMMIT_SKIP_DEPLOYS_ENFORCED
    )
    checks.append(
        MutationIsolationCheck(
            name="skip_deploys_enforced_for_source_bind",
            passed=skip_deploys_check,
            detail="COMMIT_SKIP_DEPLOYS_ENFORCED is true in source_bind_graphql",
        )
    )

    ok = isolation_ok and skip_deploys_check and not (kill_switch and preview.would_mutate)

    return RailwayMutationAuditReport(
        ok=ok,
        kill_switch_active=kill_switch,
        execution_mode=cfg.mode,
        dry_run_cannot_reach_live_adapter=dry_run_excludes_adapter,
        live_adapter_requires_enabled_mode=True,
        live_adapter_requires_authorization_token=adapter_has_gate,
        isolation_checks=checks,
        receipt_summary=receipt_summary,
        live_mutation_receipt_count=live_count,
        simulated_receipt_count=simulated_count,
        create_service_mutation_recorded=create_service_recorded,
        idempotent_replay_would_skip=preview.idempotent_replay,
        preview_would_mutate=preview.would_mutate,
        blockers=blockers,
    )
