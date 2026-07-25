# SPDX-License-Identifier: Apache-2.0
"""
Dispatch exactly one governed live mutation phase per execute invocation.

Order: create_service → connect_source → configure_env → trigger_deploy → verify_runtime (readonly).
Never runs dry-run.
"""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    phase_mutation_recorded,
    verification_readonly_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import find_phase_receipt
from aethos_core.providers.railway.execution_contract.deploy_trigger_readiness import (
    assess_deploy_trigger_readiness,
)
from aethos_core.providers.railway.execution_contract.env_configure_contract_models import (
    resolve_env_configure_groups,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_configure_env import (
    run_real_mutation_configure_env,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_trigger_deploy import (
    run_real_mutation_trigger_deploy,
)
from aethos_core.providers.railway.execution_contract.execution_readonly_runtime_verification_executor import (
    run_readonly_runtime_verification,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import find_phase_group_receipt
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    forward_live_configure_env_group_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_connect_source import (
    run_real_mutation_connect_source,
)
from aethos_core.providers.railway.execution_contract.source_binding_status import (
    assess_railway_source_binding_status,
)
from aethos_core.providers.railway.execution_contract.runtime_verification_readiness import (
    assess_runtime_verification_readiness,
)
from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    VERIFY_RUNTIME_PHASE,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_executor import (
    run_real_mutation_create_service,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_types import (
    RealMutationExecutionResult,
)

_CREATE_SERVICE = "create_service"
_CONNECT_SOURCE = "connect_source"
_CONFIGURE_ENV = "configure_env"
_TRIGGER_DEPLOY = "trigger_deploy"


def _create_service_complete(journal: dict[str, Any], *, execution_id: str) -> bool:
    if str(journal.get("railway_service_id") or "").strip():
        return True
    receipt = find_phase_receipt(execution_id=execution_id, phase=_CREATE_SERVICE)
    return phase_mutation_recorded(receipt)


def _configure_env_complete(journal: dict[str, Any], *, execution_id: str, plan: dict[str, Any]) -> bool:
    groups_to_check = resolve_env_configure_groups(plan)
    if not groups_to_check:
        return False
    groups = journal.get("env_configure_groups")
    if isinstance(groups, dict) and all(
        isinstance(groups.get(group_id), dict) and groups[group_id].get("recorded")
        for group_id, _ in groups_to_check
    ):
        return True
    for group_id, _ in groups_to_check:
        receipt = find_phase_group_receipt(
            execution_id=execution_id,
            phase=_CONFIGURE_ENV,
            receipt_group=group_id,
        )
        if not forward_live_configure_env_group_recorded(receipt):
            return False
    return True


def _trigger_deploy_complete(journal: dict[str, Any], *, execution_id: str) -> bool:
    if str(journal.get("railway_deployment_id") or "").strip():
        return True
    receipt = find_phase_receipt(execution_id=execution_id, phase=_TRIGGER_DEPLOY)
    return phase_mutation_recorded(receipt)


def _verify_runtime_complete(journal: dict[str, Any], *, execution_id: str) -> bool:
    if journal.get("runtime_verification_performed"):
        return True
    receipt = find_phase_receipt(execution_id=execution_id, phase=VERIFY_RUNTIME_PHASE)
    return verification_readonly_recorded(receipt)


def run_single_real_mutation_phase(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy: RailwayExecutionEnablementPolicy | None = None,
    user_text: str = "",
) -> RealMutationExecutionResult:
    """Run at most one live mutation phase for this execute request."""
    execution_id = str(journal.get("execution_id") or "")
    assessed = policy or assess_railway_execution_enablement_policy(plan=plan, user_text=user_text)

    if not _create_service_complete(journal, execution_id=execution_id):
        return run_real_mutation_create_service(
            journal=journal,
            plan=plan,
            policy=assessed,
            user_text=user_text,
        )

    connect_receipt = find_phase_receipt(execution_id=execution_id, phase=_CONNECT_SOURCE)
    binding_status = assess_railway_source_binding_status(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )
    if not binding_status.ready_for_env_writes:
        if assessed.allows_connect_source_mutation():
            if not phase_mutation_recorded(connect_receipt) and not journal.get("github_source_bound"):
                return run_real_mutation_connect_source(
                    journal=journal,
                    plan=plan,
                    policy=assessed,
                    user_text=user_text,
                )
        elif not phase_mutation_recorded(connect_receipt) and not journal.get("github_source_bound"):
            return RealMutationExecutionResult(
                journal=journal,
                policy_blocked=True,
                detail=(
                    "create_service is complete; connect_source is disabled "
                    "(set RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED=true)."
                ),
                errors=["connect_source_disabled"],
            )

    binding_status = assess_railway_source_binding_status(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
    )
    if binding_status.ready_for_env_writes and assessed.allows_configure_env_mutation():
        if not _configure_env_complete(journal, execution_id=execution_id, plan=plan):
            return run_real_mutation_configure_env(
                journal=journal,
                plan=plan,
                policy=assessed,
                user_text=user_text,
            )

    if binding_status.ready_for_env_writes and not assessed.allows_configure_env_mutation():
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail=(
                "connect_source is complete; configure_env is disabled "
                "(set RAILWAY_GREENFIELD_CONFIGURE_ENV_ENABLED=true)."
            ),
            errors=["configure_env_disabled"],
        )

    if not _configure_env_complete(journal, execution_id=execution_id, plan=plan):
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="configure_env must complete before trigger_deploy.",
            errors=["configure_env_incomplete"],
        )

    deploy_readiness = assess_deploy_trigger_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )

    if not _trigger_deploy_complete(journal, execution_id=execution_id):
        if deploy_readiness.ready_for_deploy_trigger and assessed.allows_trigger_deploy_mutation():
            return run_real_mutation_trigger_deploy(
                journal=journal,
                plan=plan,
                policy=assessed,
                user_text=user_text,
            )
        if not assessed.allows_trigger_deploy_mutation():
            return RealMutationExecutionResult(
                journal=journal,
                policy_blocked=True,
                detail=(
                    "configure_env is complete; trigger_deploy is disabled "
                    "(set RAILWAY_GREENFIELD_TRIGGER_DEPLOY_ENABLED=true)."
                ),
                errors=["trigger_deploy_disabled"],
            )
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Deploy trigger readiness gate not satisfied.",
            errors=list(deploy_readiness.blockers),
        )

    verify_readiness = assess_runtime_verification_readiness(
        plan=plan,
        journal=journal,
        execution_id=execution_id,
        user_text=user_text,
    )

    if not _verify_runtime_complete(journal, execution_id=execution_id):
        if verify_readiness.ready_for_runtime_verification and assessed.allows_verify_runtime_readonly():
            return run_readonly_runtime_verification(
                journal=journal,
                plan=plan,
                policy=assessed,
                user_text=user_text,
            )
        if not assessed.allows_verify_runtime_readonly():
            return RealMutationExecutionResult(
                journal=journal,
                policy_blocked=True,
                detail=(
                    "trigger_deploy is complete; verify_runtime is disabled "
                    "(set RAILWAY_GREENFIELD_VERIFY_RUNTIME_ENABLED=true)."
                ),
                errors=["verify_runtime_disabled"],
            )
        return RealMutationExecutionResult(
            journal=journal,
            policy_blocked=True,
            detail="Runtime verification readiness gate not satisfied.",
            errors=list(verify_readiness.blockers),
        )

    return RealMutationExecutionResult(
        journal=journal,
        mutation_performed=False,
        idempotent_replay=True,
        service_id=str(journal.get("railway_service_id") or ""),
        detail="All governed phases complete; idempotent replay.",
    )
