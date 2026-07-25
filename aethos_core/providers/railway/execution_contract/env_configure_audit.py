# SPDX-License-Identifier: Apache-2.0
"""FIX 112B — configure_env verification audit and safety guards."""

from __future__ import annotations

import importlib.util
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aethos_core.operations.mutations.secrets import parse_env_var_from_request
from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    CONFIGURE_ENV_FORWARD_PHASE,
    ENV_CONFIGURE_GROUPS,
)
from aethos_core.providers.railway.execution_contract.env_configure_rollback_contract import (
    build_env_configure_rollback_contract,
    group_version_fingerprint_for_plan,
)
from aethos_core.providers.railway.execution_contract.env_configure_verification import (
    EnvConfigureVerification,
    verify_env_configure_readonly,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_MUTATION_SKIPPED,
    STATUS_MUTATION_SUCCESS,
    STATUS_SIMULATED_SUCCESS,
    forward_live_configure_env_group_recorded,
    normalize_receipt_status,
    receipt_is_simulated,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    find_phase_group_receipt,
    list_execution_receipts,
)
from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
    COMMIT_SKIP_DEPLOYS_ENFORCED,
)


@dataclass
class ConfigureEnvGroupReceiptAudit:
    group_id: str
    receipt_found: bool
    status: str = ""
    mutation_performed: bool = False
    is_simulated: bool = False
    is_live_mutation: bool = False
    idempotent_replay: bool = False
    env_var_names: list[str] = field(default_factory=list)
    ok: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass
class EnvConfigureIdempotentProof:
    group_id: str
    journal_recorded: bool
    receipt_recorded: bool
    version_fingerprint: str = ""
    would_skip_on_replay: bool = False
    detail: str = ""


@dataclass
class RailwayEnvConfigureAuditReport:
    ok: bool
    skip_deploys_enforced_in_code: bool
    env_only_stage_validation: bool
    no_source_keys_in_env_adapter: bool
    no_secret_values_in_receipt_fields: bool
    secure_store_only_resolution: bool
    blocks_chat_secrets_in_executor: bool
    blocks_local_env_resolution: bool
    no_deploy_trigger_in_adapter: bool
    group_receipts: list[ConfigureEnvGroupReceiptAudit] = field(default_factory=list)
    idempotent_proofs: list[EnvConfigureIdempotentProof] = field(default_factory=list)
    rollback_contract_visible: bool = False
    rollback_plan_ready: bool = False
    verification: EnvConfigureVerification | None = None
    forbidden_live_phases: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "skip_deploys_enforced_in_code": self.skip_deploys_enforced_in_code,
            "env_only_stage_validation": self.env_only_stage_validation,
            "no_source_keys_in_env_adapter": self.no_source_keys_in_env_adapter,
            "no_secret_values_in_receipt_fields": self.no_secret_values_in_receipt_fields,
            "secure_store_only_resolution": self.secure_store_only_resolution,
            "blocks_chat_secrets_in_executor": self.blocks_chat_secrets_in_executor,
            "blocks_local_env_resolution": self.blocks_local_env_resolution,
            "no_deploy_trigger_in_adapter": self.no_deploy_trigger_in_adapter,
            "group_receipts": [
                {
                    "group_id": g.group_id,
                    "receipt_found": g.receipt_found,
                    "status": g.status,
                    "mutation_performed": g.mutation_performed,
                    "is_simulated": g.is_simulated,
                    "is_live_mutation": g.is_live_mutation,
                    "idempotent_replay": g.idempotent_replay,
                    "env_var_names": list(g.env_var_names),
                    "ok": g.ok,
                    "errors": list(g.errors),
                }
                for g in self.group_receipts
            ],
            "idempotent_proofs": [
                {
                    "group_id": p.group_id,
                    "journal_recorded": p.journal_recorded,
                    "receipt_recorded": p.receipt_recorded,
                    "version_fingerprint": p.version_fingerprint,
                    "would_skip_on_replay": p.would_skip_on_replay,
                    "detail": p.detail,
                }
                for p in self.idempotent_proofs
            ],
            "rollback_contract_visible": self.rollback_contract_visible,
            "rollback_plan_ready": self.rollback_plan_ready,
            "verification": self.verification.to_dict() if self.verification else None,
            "forbidden_live_phases": list(self.forbidden_live_phases),
            "blockers": list(self.blockers),
        }


def _module_source_path(module_name: str) -> Path | None:
    spec = importlib.util.find_spec(module_name)
    if spec is None or not spec.origin:
        return None
    return Path(spec.origin)


def _adapter_static_safety() -> tuple[bool, bool, bool, bool, bool, bool, bool]:
    graphql_path = _module_source_path(
        "aethos_core.providers.railway.greenfield_adapters.env_configure_graphql"
    )
    adapter_path = _module_source_path(
        "aethos_core.providers.railway.greenfield_adapters.configure_env_adapter"
    )
    resolve_path = _module_source_path(
        "aethos_core.providers.railway.env_value_readiness.env_secure_resolution"
    )
    executor_path = _module_source_path(
        "aethos_core.providers.railway.execution_contract.execution_real_mutation_configure_env"
    )
    graphql_source = graphql_path.read_text(encoding="utf-8") if graphql_path else ""
    adapter_source = adapter_path.read_text(encoding="utf-8") if adapter_path else ""
    resolve_source = resolve_path.read_text(encoding="utf-8") if resolve_path else ""
    executor_source = executor_path.read_text(encoding="utf-8") if executor_path else ""

    skip_deploys = COMMIT_SKIP_DEPLOYS_ENFORCED and "skipDeploys" in graphql_source
    env_only = "validate_stage_input_env_only" in graphql_source
    no_source = '"source"' not in adapter_source
    names_only_read = "read_service_env_var_names" in graphql_source and "names" in graphql_source
    secure_only = "_FORBIDDEN_SOURCES" in resolve_source and "local_env_dev_only" in resolve_source
    blocks_chat = "parse_env_var_from_request" in executor_source and "chat_secrets_forbidden" in executor_source
    no_deploy = (
        "trigger_deploy" not in adapter_source
        and "serviceInstanceRedeploy" not in adapter_source
        and "skip_deploys" in adapter_source.lower()
    )
    _ = names_only_read
    no_values_in_receipts = "env_var_names" in executor_source and "receipt_group" in executor_source
    return skip_deploys, env_only, no_source, no_values_in_receipts, secure_only, blocks_chat, no_deploy


def audit_configure_env_group_receipt(
    *,
    execution_id: str,
    group_id: str,
) -> ConfigureEnvGroupReceiptAudit:
    receipt = find_phase_group_receipt(
        execution_id=execution_id,
        phase=CONFIGURE_ENV_FORWARD_PHASE,
        receipt_group=group_id,
    )
    if not receipt:
        return ConfigureEnvGroupReceiptAudit(
            group_id=group_id,
            receipt_found=False,
            errors=[f"configure_env receipt missing for group `{group_id}`"],
        )
    normalized = normalize_receipt_status(dict(receipt))
    status = str(normalized.get("status") or "")
    mutation_performed = bool(normalized.get("mutation_performed"))
    is_simulated = receipt_is_simulated(normalized)
    is_live = forward_live_configure_env_group_recorded(normalized)
    idempotent = status == STATUS_MUTATION_SKIPPED or bool(normalized.get("replayed"))
    names = [str(n) for n in normalized.get("env_var_names") or []]
    detail = str(normalized.get("detail") or "")
    errors: list[str] = []
    if is_simulated and status == STATUS_SIMULATED_SUCCESS:
        errors.append("configure_env_receipt_is_simulated_not_live")
    if re.search(r"sk-[a-zA-Z0-9]{8,}", detail):
        errors.append("receipt_detail_may_contain_secret_value")
    ok = is_live and not errors
    return ConfigureEnvGroupReceiptAudit(
        group_id=group_id,
        receipt_found=True,
        status=status,
        mutation_performed=mutation_performed,
        is_simulated=is_simulated,
        is_live_mutation=is_live,
        idempotent_replay=idempotent,
        env_var_names=names,
        ok=ok,
        errors=errors,
    )


def build_idempotent_replay_proofs(
    *,
    plan: dict[str, Any],
    journal: dict[str, Any],
    execution_id: str,
) -> list[EnvConfigureIdempotentProof]:
    groups_state = journal.get("env_configure_groups") if isinstance(journal.get("env_configure_groups"), dict) else {}
    proofs: list[EnvConfigureIdempotentProof] = []
    for group_id, env_names in ENV_CONFIGURE_GROUPS:
        row = groups_state.get(group_id) if isinstance(groups_state.get(group_id), dict) else {}
        journal_recorded = bool(row.get("recorded"))
        fingerprint = str(row.get("version_fingerprint") or "")
        if not fingerprint:
            fingerprint = group_version_fingerprint_for_plan(
                plan=plan,
                group_id=group_id,
                env_names=env_names,
            )
        receipt = find_phase_group_receipt(
            execution_id=execution_id,
            phase=CONFIGURE_ENV_FORWARD_PHASE,
            receipt_group=group_id,
        )
        receipt_recorded = receipt is not None
        would_skip = journal_recorded and receipt_recorded and (
            str(receipt.get("status") or "") in {STATUS_MUTATION_SUCCESS, STATUS_MUTATION_SKIPPED}
            if receipt
            else False
        )
        proofs.append(
            EnvConfigureIdempotentProof(
                group_id=group_id,
                journal_recorded=journal_recorded,
                receipt_recorded=receipt_recorded,
                version_fingerprint=fingerprint,
                would_skip_on_replay=would_skip,
                detail=(
                    f"group `{group_id}` would skip replay (journal+receipt+fingerprint)"
                    if would_skip
                    else f"group `{group_id}` not yet idempotent-safe"
                ),
            )
        )
    return proofs


def audit_configure_env_adapter_safety() -> dict[str, bool]:
    """Legacy static-only audit (FIX 112). Prefer build_railway_env_configure_audit_report."""
    skip, env_only, no_source, no_values, secure, blocks_chat, no_deploy = _adapter_static_safety()
    return {
        "skip_deploys_enforced": skip,
        "env_only_stage_validation": env_only,
        "no_source_keys_in_env_adapter": no_source,
        "no_secret_values_in_receipt_fields": no_values,
        "secure_store_only_resolution": secure,
        "blocks_chat_secrets_in_executor": blocks_chat,
        "blocks_local_env_resolution": secure,
        "no_deploy_trigger_in_adapter": no_deploy,
    }


def build_railway_env_configure_audit_report(
    *,
    plan: dict[str, Any] | None = None,
    journal: dict[str, Any] | None = None,
    execution_id: str = "",
    user_text: str = "",
) -> RailwayEnvConfigureAuditReport:
    plan = plan or {}
    journal = journal or {}
    execution_id = execution_id or str(journal.get("execution_id") or "")
    user_text = user_text or ""

    (
        skip_deploys,
        env_only,
        no_source,
        no_values,
        secure_only,
        blocks_chat,
        no_deploy,
    ) = _adapter_static_safety()

    chat_in_request = parse_env_var_from_request(user_text) is not None

    group_receipts = [
        audit_configure_env_group_receipt(execution_id=execution_id, group_id=group_id)
        for group_id, _ in ENV_CONFIGURE_GROUPS
        if execution_id
    ]

    idempotent_proofs = (
        build_idempotent_replay_proofs(plan=plan, journal=journal, execution_id=execution_id)
        if execution_id
        else []
    )

    rollback_contract = build_env_configure_rollback_contract(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )
    rollback_visible = bool(journal.get("env_configure_rollback_plan") or journal.get("rollback_journal"))

    verification: EnvConfigureVerification | None = None
    service_id = str(journal.get("railway_service_id") or "")
    environment_id = str(journal.get("railway_environment_id") or "")
    if service_id and environment_id:
        journal_names: list[str] = []
        configured = journal.get("env_vars_configured")
        if isinstance(configured, dict):
            for group in configured.get("groups", {}).values():
                if isinstance(group, dict):
                    journal_names.extend(str(n) for n in group.get("env_names") or [])
        verification = verify_env_configure_readonly(
            environment_id=environment_id,
            service_id=service_id,
            journal_env_names=journal_names,
        )

    forbidden: list[str] = []
    if execution_id:
        for receipt in list_execution_receipts(execution_id=execution_id):
            phase = str(receipt.get("phase") or "")
            if phase == "trigger_deploy" and bool(receipt.get("mutation_performed")):
                forbidden.append(phase)

    blockers: list[str] = []
    if chat_in_request:
        blockers.append("chat_secrets_in_user_text")
    if not blocks_chat:
        blockers.append("executor_missing_chat_secret_block")
    if not secure_only:
        blockers.append("local_env_resolution_not_blocked")
    if not no_deploy:
        blockers.append("deploy_trigger_path_in_adapter")
    if not skip_deploys:
        blockers.append("skip_deploys_not_enforced")
    if forbidden:
        blockers.append("unexpected_live_deploy_phase")
    for group_audit in group_receipts:
        if group_audit.receipt_found and not group_audit.ok:
            blockers.append(f"receipt_audit_failed_{group_audit.group_id}")
    has_live_configure_receipts = any(g.receipt_found and g.is_live_mutation for g in group_receipts)
    if verification and not verification.verified and has_live_configure_receipts:
        blockers.append("minimum_secrets_not_verified")
    if not rollback_visible:
        blockers.append("rollback_contract_not_visible")

    ok = (
        not chat_in_request
        and blocks_chat
        and secure_only
        and no_deploy
        and skip_deploys
        and env_only
        and no_source
        and not forbidden
        and rollback_visible
        and all(g.ok or not g.receipt_found for g in group_receipts)
        and not blockers
    )

    return RailwayEnvConfigureAuditReport(
        ok=ok,
        skip_deploys_enforced_in_code=skip_deploys,
        env_only_stage_validation=env_only,
        no_source_keys_in_env_adapter=no_source,
        no_secret_values_in_receipt_fields=no_values,
        secure_store_only_resolution=secure_only,
        blocks_chat_secrets_in_executor=blocks_chat and not chat_in_request,
        blocks_local_env_resolution=secure_only,
        no_deploy_trigger_in_adapter=no_deploy,
        group_receipts=group_receipts,
        idempotent_proofs=idempotent_proofs,
        rollback_contract_visible=rollback_visible,
        rollback_plan_ready=rollback_contract.rollback_plan_ready,
        verification=verification,
        forbidden_live_phases=forbidden,
        blockers=blockers,
    )
