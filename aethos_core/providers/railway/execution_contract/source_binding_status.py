# SPDX-License-Identifier: Apache-2.0
"""FIX 109B — `show railway source binding status` assessment."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    phase_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_receipt,
)
from aethos_core.providers.railway.execution_contract.source_binding_audit import (
    audit_connect_source_receipt,
    build_connect_source_rollback_plan,
)
from aethos_core.providers.railway.execution_contract.source_binding_verification import (
    SourceBindingVerification,
    verify_source_binding_readonly,
)
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    COMMIT_SKIP_DEPLOYS_ENFORCED,
)


@dataclass(frozen=True)
class RailwaySourceBindingStatus:
    binding_recorded_on_journal: bool
    journal_repository: str
    journal_branch: str
    service_id: str
    environment_id: str
    connect_source_receipt_status: str
    mutation_performed: bool
    idempotent_replay: bool
    skip_deploys_enforced: bool
    readonly_verification: SourceBindingVerification | None
    rollback_plan_available: bool
    ready_for_env_writes: bool
    blockers: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_recorded_on_journal": self.binding_recorded_on_journal,
            "journal_repository": self.journal_repository,
            "journal_branch": self.journal_branch,
            "service_id": self.service_id,
            "environment_id": self.environment_id,
            "connect_source_receipt_status": self.connect_source_receipt_status,
            "mutation_performed": self.mutation_performed,
            "idempotent_replay": self.idempotent_replay,
            "skip_deploys_enforced": self.skip_deploys_enforced,
            "readonly_verification": (
                self.readonly_verification.to_dict() if self.readonly_verification else None
            ),
            "rollback_plan_available": self.rollback_plan_available,
            "ready_for_env_writes": self.ready_for_env_writes,
            "blockers": list(self.blockers),
            "messages": list(self.messages),
        }


def assess_railway_source_binding_status(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
) -> RailwaySourceBindingStatus:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")

    binding = journal.get("github_source_bound") if isinstance(journal.get("github_source_bound"), dict) else {}
    journal_repo = str(binding.get("repository") or "")
    journal_branch = str(binding.get("branch") or "")
    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")

    receipt = find_phase_receipt(execution_id=execution_id, phase="connect_source") if execution_id else None
    receipt_audit = audit_connect_source_receipt(execution_id=execution_id) if execution_id else None
    receipt_status = str((receipt or {}).get("status") or "—")
    mutation_performed = bool((receipt or {}).get("mutation_performed"))
    idempotent = bool(journal_repo) or phase_mutation_recorded(receipt)

    verification: SourceBindingVerification | None = None
    if service_id and environment_id and str(plan.get("repo") or ""):
        verification = verify_source_binding_readonly(
            environment_id=environment_id,
            service_id=service_id,
            expected_repository=str(plan.get("repo") or ""),
            expected_branch=str(plan.get("branch") or "main"),
            journal_binding={"repository": journal_repo, "branch": journal_branch} if journal_repo else None,
        )

    rollback_plan = build_connect_source_rollback_plan(journal=journal)
    blockers: list[str] = []
    messages: list[str] = []

    if not service_id:
        blockers.append("create_service_required")
        messages.append("create_service must complete before source binding status is meaningful.")
    binding_recorded = bool(journal_repo) or phase_mutation_recorded(receipt)
    if not binding_recorded:
        blockers.append("connect_source_not_recorded")
        messages.append("connect_source has not been recorded on this execution.")
    if verification and not verification.verified:
        blockers.append("readonly_verification_pending")
        messages.append(verification.detail)
    if receipt_audit and receipt_audit.receipt_found and receipt_audit.is_simulated:
        blockers.append("receipt_is_simulated")
        messages.append("connect_source receipt is simulated — not a live binding.")

    ready_for_env = (
        binding_recorded
        and (verification is None or verification.verified)
        and not blockers
    )
    if ready_for_env:
        from aethos_core.config import get_settings

        if bool(getattr(get_settings(), "railway_greenfield_configure_env_enabled", False)):
            messages.append(
                "Source binding verification passed — configure_env may run when execution_mode=enabled."
            )
        else:
            messages.append(
                "Source binding verification passed — env writes remain disabled "
                "(railway_greenfield_configure_env_enabled=false)."
            )

    return RailwaySourceBindingStatus(
        binding_recorded_on_journal=bool(journal_repo),
        journal_repository=journal_repo,
        journal_branch=journal_branch,
        service_id=service_id,
        environment_id=environment_id,
        connect_source_receipt_status=receipt_status,
        mutation_performed=mutation_performed,
        idempotent_replay=idempotent,
        skip_deploys_enforced=COMMIT_SKIP_DEPLOYS_ENFORCED,
        readonly_verification=verification,
        rollback_plan_available=rollback_plan is not None,
        ready_for_env_writes=ready_for_env,
        blockers=blockers,
        messages=messages,
    )
