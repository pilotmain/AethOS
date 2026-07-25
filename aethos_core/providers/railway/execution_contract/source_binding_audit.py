# SPDX-License-Identifier: Apache-2.0
"""FIX 109B — Source binding audit, receipt checks, and safety guards."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_MUTATION_SKIPPED,
    STATUS_MUTATION_SUCCESS,
    STATUS_SIMULATED_SUCCESS,
    normalize_receipt_status,
    phase_mutation_recorded,
    receipt_is_simulated,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
    list_execution_receipts,
)
from aethos_core.providers.railway.execution_contract.source_binding_verification import (
    SourceBindingVerification,
    verify_source_binding_readonly,
)
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    COMMIT_SKIP_DEPLOYS_ENFORCED,
)


@dataclass
class ConnectSourceReceiptAudit:
    receipt_found: bool
    phase: str = "connect_source"
    status: str = ""
    mutation_performed: bool = False
    is_simulated: bool = False
    is_live_mutation: bool = False
    detail_mentions_skip_deploys: bool = False
    idempotent_replay: bool = False
    ok: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class SourceBindingRollbackPlan:
    execution_id: str
    service_id: str
    environment_id: str
    repository: str
    branch: str
    rollback_action: str = "disconnect_repo_source"
    steps: list[str] = field(default_factory=list)
    executable: bool = False
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "service_id": self.service_id,
            "environment_id": self.environment_id,
            "repository": self.repository,
            "branch": self.branch,
            "rollback_action": self.rollback_action,
            "steps": list(self.steps),
            "executable": self.executable,
            "detail": self.detail,
        }


@dataclass
class RailwaySourceBindingAuditReport:
    ok: bool
    skip_deploys_enforced_in_code: bool
    stage_input_source_only_guard: bool
    no_env_write_paths_in_adapter: bool
    no_deploy_trigger_in_adapter: bool
    connect_source_receipt: ConnectSourceReceiptAudit
    idempotent_replay_would_skip: bool
    forbidden_forward_phases_with_live_mutation: list[str] = field(default_factory=list)
    verification: SourceBindingVerification | None = None
    rollback_plan: SourceBindingRollbackPlan | None = None
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "skip_deploys_enforced_in_code": self.skip_deploys_enforced_in_code,
            "stage_input_source_only_guard": self.stage_input_source_only_guard,
            "no_env_write_paths_in_adapter": self.no_env_write_paths_in_adapter,
            "no_deploy_trigger_in_adapter": self.no_deploy_trigger_in_adapter,
            "connect_source_receipt": {
                "receipt_found": self.connect_source_receipt.receipt_found,
                "phase": self.connect_source_receipt.phase,
                "status": self.connect_source_receipt.status,
                "mutation_performed": self.connect_source_receipt.mutation_performed,
                "is_simulated": self.connect_source_receipt.is_simulated,
                "is_live_mutation": self.connect_source_receipt.is_live_mutation,
                "detail_mentions_skip_deploys": self.connect_source_receipt.detail_mentions_skip_deploys,
                "idempotent_replay": self.connect_source_receipt.idempotent_replay,
                "ok": self.connect_source_receipt.ok,
                "errors": list(self.connect_source_receipt.errors),
            },
            "idempotent_replay_would_skip": self.idempotent_replay_would_skip,
            "forbidden_forward_phases_with_live_mutation": list(
                self.forbidden_forward_phases_with_live_mutation
            ),
            "verification": self.verification.to_dict() if self.verification else None,
            "rollback_plan": self.rollback_plan.to_dict() if self.rollback_plan else None,
            "blockers": list(self.blockers),
        }


def _module_source_path(module_name: str) -> Path | None:
    spec = importlib.util.find_spec(module_name)
    if spec is None or not spec.origin:
        return None
    return Path(spec.origin)


def audit_connect_source_receipt(*, execution_id: str) -> ConnectSourceReceiptAudit:
    receipt = find_phase_receipt(execution_id=execution_id, phase="connect_source")
    if not receipt:
        return ConnectSourceReceiptAudit(
            receipt_found=False,
            errors=["connect_source_receipt_missing"],
        )
    normalized = normalize_receipt_status(dict(receipt))
    status = str(normalized.get("status") or "")
    mutation_performed = bool(normalized.get("mutation_performed"))
    is_simulated = receipt_is_simulated(normalized)
    is_live = status in {STATUS_MUTATION_SUCCESS, STATUS_MUTATION_SKIPPED} or mutation_performed
    detail = str(normalized.get("detail") or "").lower()
    mentions_skip = "skipdeploys" in detail or "skip_deploys" in detail
    idempotent = status == STATUS_MUTATION_SKIPPED or bool(normalized.get("replayed"))
    errors: list[str] = []
    if is_simulated and status == STATUS_SIMULATED_SUCCESS:
        errors.append("connect_source_receipt_is_simulated_not_live")
    if mutation_performed and not mentions_skip and status == STATUS_MUTATION_SUCCESS:
        errors.append("receipt_missing_skip_deploys_detail")
    ok = True
    if is_simulated and status == STATUS_SIMULATED_SUCCESS:
        ok = False
    return ConnectSourceReceiptAudit(
        receipt_found=True,
        status=status,
        mutation_performed=mutation_performed,
        is_simulated=is_simulated,
        is_live_mutation=is_live,
        detail_mentions_skip_deploys=mentions_skip or status == STATUS_MUTATION_SKIPPED,
        idempotent_replay=idempotent,
        ok=ok,
        errors=errors,
    )


def build_connect_source_rollback_plan(
    *,
    journal: dict[str, Any] | None,
) -> SourceBindingRollbackPlan | None:
    journal = journal or {}
    execution_id = str(journal.get("execution_id") or "")
    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    binding = journal.get("github_source_bound") if isinstance(journal.get("github_source_bound"), dict) else {}
    repo = str(binding.get("repository") or journal.get("repo") or "")
    branch = str(binding.get("branch") or "main")
    if not execution_id or not service_id:
        return None
    return SourceBindingRollbackPlan(
        execution_id=execution_id,
        service_id=service_id,
        environment_id=environment_id,
        repository=repo,
        branch=branch,
        steps=[
            "disconnect_repo_source — remove GitHub repo binding (FIX 111 live adapter when enabled)",
            "verify readonly environment config shows no repo source",
            "mark_execution_rolled_back",
        ],
        executable=False,
        detail="Live rollback via `execute railway source binding rollback` when disconnect flag enabled.",
    )


def _adapter_safety_checks() -> tuple[bool, bool, bool]:
    graphql_path = _module_source_path(
        "aethos_core.providers.railway.greenfield_adapters.source_bind_graphql"
    )
    adapter_path = _module_source_path(
        "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter"
    )
    skip_enforced = COMMIT_SKIP_DEPLOYS_ENFORCED
    stage_guard = bool(
        graphql_path and "validate_stage_input_source_only" in graphql_path.read_text(encoding="utf-8")
    )
    adapter_source = adapter_path.read_text(encoding="utf-8") if adapter_path else ""
    no_env = "variables" not in adapter_source or "sharedVariables" not in adapter_source
    no_deploy = "serviceInstanceRedeploy" not in adapter_source and "trigger_deploy" not in adapter_source
    no_env_writes = no_env and "set_env" not in adapter_source.lower()
    return skip_enforced, stage_guard, no_env_writes and no_deploy


def build_railway_source_binding_audit_report(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
) -> RailwaySourceBindingAuditReport:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")

    skip_enforced, stage_guard, adapter_safe = _adapter_safety_checks()
    receipt_audit = (
        audit_connect_source_receipt(execution_id=execution_id) if execution_id else ConnectSourceReceiptAudit(
            receipt_found=False,
            errors=["no_execution_id"],
        )
    )

    idempotent_replay = bool(journal.get("github_source_bound")) or (
        execution_id
        and phase_mutation_recorded(find_phase_receipt(execution_id=execution_id, phase="connect_source"))
    )

    forbidden_live: list[str] = []
    if execution_id:
        for phase in ("configure_env", "trigger_deploy", "verify_runtime"):
            receipt = find_phase_receipt(execution_id=execution_id, phase=phase)
            if receipt and bool(receipt.get("mutation_performed")):
                forbidden_live.append(phase)

    verification: SourceBindingVerification | None = None
    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    if service_id and environment_id and str(plan.get("repo") or ""):
        journal_binding = journal.get("github_source_bound")
        binding_dict = dict(journal_binding) if isinstance(journal_binding, dict) else None
        verification = verify_source_binding_readonly(
            environment_id=environment_id,
            service_id=service_id,
            expected_repository=str(plan.get("repo") or ""),
            expected_branch=str(plan.get("branch") or "main"),
            journal_binding=binding_dict,
        )

    rollback_plan = build_connect_source_rollback_plan(journal=journal)

    blockers: list[str] = []
    if not skip_enforced:
        blockers.append("skip_deploys_not_enforced")
    if forbidden_live:
        blockers.append("unexpected_live_forward_phases")
    if receipt_audit.receipt_found and not receipt_audit.ok:
        blockers.append("connect_source_receipt_audit_failed")

    ok = (
        skip_enforced
        and stage_guard
        and adapter_safe
        and not forbidden_live
        and (not receipt_audit.receipt_found or receipt_audit.ok)
    )

    return RailwaySourceBindingAuditReport(
        ok=ok,
        skip_deploys_enforced_in_code=skip_enforced,
        stage_input_source_only_guard=stage_guard,
        no_env_write_paths_in_adapter=adapter_safe,
        no_deploy_trigger_in_adapter=adapter_safe,
        connect_source_receipt=receipt_audit,
        idempotent_replay_would_skip=idempotent_replay,
        forbidden_forward_phases_with_live_mutation=forbidden_live,
        verification=verification,
        rollback_plan=rollback_plan,
        blockers=blockers,
    )
