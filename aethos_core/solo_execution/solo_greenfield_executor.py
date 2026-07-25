# SPDX-License-Identifier: Apache-2.0
"""Solo greenfield Railway execution — auto-approve and run governed phases."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from aethos_core.providers.railway.execution_contract.execution_journal import get_or_create_execution_journal
from aethos_core.providers.railway.execution_contract.execution_real_mutation_dispatch import (
    run_single_real_mutation_phase,
)
from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_flow import (
    approve_railway_greenfield_preflight,
)
from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_gate import GreenfieldApprovalError
from aethos_core.providers.railway.greenfield_deployment.greenfield_flow import RailwayGreenfieldFlowResult
from aethos_core.security.secret_redaction import redact_text
from aethos_core.solo_execution.solo_execution_mode import (
    build_solo_railway_execution_policy,
    compose_solo_greenfield_intro,
    is_solo_execution_mode_enabled,
    validate_solo_greenfield_eligibility,
)
from aethos_core.solo_execution.solo_final_report import (
    build_solo_final_report_payload,
    compose_solo_chat_reply,
    compose_solo_greenfield_final_report,
)

_SOLO_PREFLIGHT_FALLBACK_BLOCKERS = frozenset(
    {
        "SOLO_MUTATION_EXECUTION_DISABLED",
        "SOLO_EXECUTION_DISABLED",
    }
)


@dataclass
class SoloGreenfieldExecutionResult:
    flow: RailwayGreenfieldFlowResult
    journal: dict[str, Any] = field(default_factory=dict)


def maybe_run_solo_greenfield_execution(
    *,
    user_text: str,
    session_id: str,
    plan: dict[str, Any],
    env_report: dict[str, Any],
    git_remote: dict[str, Any],
    local_source: dict[str, Any],
    inspection: dict[str, Any],
    preflight_job_id: str,
    preflight_id: str,
    local_report: str,
    git_report: str,
    target_report: str,
    env_report_text: str,
) -> RailwayGreenfieldFlowResult | None:
    if not is_solo_execution_mode_enabled():
        return None

    from aethos_core.governance.approval_privacy_governance import solo_auto_approve_preflight

    if not solo_auto_approve_preflight():
        return None

    eligibility = validate_solo_greenfield_eligibility(
        plan=plan,
        env_report=env_report,
        git_remote=git_remote,
        provider="railway",
        user_text=user_text,
    )
    if not eligibility.ok and (eligibility.blocker_code or "") in _SOLO_PREFLIGHT_FALLBACK_BLOCKERS:
        return None

    result = run_solo_greenfield_execution(
        user_text=user_text,
        session_id=session_id,
        plan=plan,
        env_report=env_report,
        git_remote=git_remote,
        local_source=local_source,
        inspection=inspection,
        preflight_job_id=preflight_job_id,
        preflight_id=preflight_id,
        local_report=local_report,
        git_report=git_report,
        target_report=target_report,
        env_report_text=env_report_text,
    )
    return result.flow


def run_solo_greenfield_execution(
    *,
    user_text: str,
    session_id: str,
    plan: dict[str, Any],
    env_report: dict[str, Any],
    git_remote: dict[str, Any],
    local_source: dict[str, Any],
    inspection: dict[str, Any],
    preflight_job_id: str,
    preflight_id: str,
    local_report: str,
    git_report: str,
    target_report: str,
    env_report_text: str,
) -> SoloGreenfieldExecutionResult:
    eligibility = validate_solo_greenfield_eligibility(
        plan=plan,
        env_report=env_report,
        git_remote=git_remote,
        provider="railway",
        user_text=user_text,
    )
    if not eligibility.ok:
        code = eligibility.blocker_code or "SOLO_EXECUTION_BLOCKED"
        return SoloGreenfieldExecutionResult(
            flow=_blocked_flow(
                code=code,
                detail=eligibility.detail or "Solo execution blocked.",
                required_action=eligibility.required_action,
                safe_next_command=eligibility.safe_next_command,
            )
        )

    intro = compose_solo_greenfield_intro(
        plan=plan,
        git_remote=git_remote,
        env_report=env_report,
        local_source=local_source,
        inspection=inspection,
    )

    try:
        approve_railway_greenfield_preflight(
            preflight_job_id,
            session_id=session_id,
            spawn_orchestration=False,
        )
    except GreenfieldApprovalError as exc:
        gate = exc.result
        return SoloGreenfieldExecutionResult(
            flow=_blocked_flow(
                code=str(gate.failure_state or "SOLO_APPROVAL_BLOCKED"),
                detail=gate.detail or "Greenfield approval blocked.",
                required_action=gate.required_action or "Resolve the blocker and retry.",
                safe_next_command=gate.safe_next_command or user_text,
            )
        )

    journal, _created = get_or_create_execution_journal(
        plan=plan,
        session_id=session_id,
        initial_state="execution_locked",
        approval={"mode": "solo_execution", "preflight_id": preflight_id, "job_id": preflight_job_id},
    )
    from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal

    if not journal.get("rollback_journal"):
        journal = attach_rollback_journal(journal)
    policy = build_solo_railway_execution_policy(plan=plan, user_text=user_text)
    journal, execution_status, blocker = _run_solo_phase_loop(
        journal=journal,
        plan=plan,
        policy=policy,
        user_text=user_text,
    )

    if blocker:
        report = compose_solo_greenfield_final_report(
            plan=plan,
            git_remote=git_remote,
            journal=journal,
            env_report=env_report,
            preflight_id=preflight_id,
            preflight_job_id=preflight_job_id,
            execution_status="failed",
            logs_summary=blocker.get("detail", ""),
            next_action=blocker.get("required_action", ""),
        )
        reply = compose_solo_chat_reply(
            plan=plan,
            git_remote=git_remote,
            journal=journal,
            env_report=env_report,
            execution_status="failed",
            blocker_code=str(blocker.get("code") or "SOLO_EXECUTION_FAILED"),
            blocker_detail=str(blocker.get("detail") or ""),
        )
        return SoloGreenfieldExecutionResult(
            flow=RailwayGreenfieldFlowResult(
                ok=False,
                blocked=True,
                blocker_code=str(blocker.get("code") or "SOLO_EXECUTION_FAILED"),
                blocker_detail=str(blocker.get("detail") or ""),
                safe_next_command=str(blocker.get("safe_next_command") or ""),
                reply=redact_text(reply),
                intent="railway_greenfield_solo_execution_blocked",
                preflight_job_id=preflight_job_id,
                artifacts={
                    "solo_execution": True,
                    "journal": _safe_journal(journal),
                    "solo_final_report": build_solo_final_report_payload(
                        full_report=report,
                        plan=plan,
                        journal=journal,
                        env_report=env_report,
                        execution_status="failed",
                    ),
                },
            ),
            journal=journal,
        )

    report = compose_solo_greenfield_final_report(
        plan=plan,
        git_remote=git_remote,
        journal=journal,
        env_report=env_report,
        preflight_id=preflight_id,
        preflight_job_id=preflight_job_id,
        execution_status=execution_status,
    )
    reply = compose_solo_chat_reply(
        plan=plan,
        git_remote=git_remote,
        journal=journal,
        env_report=env_report,
        execution_status=execution_status,
    )
    from aethos_core.operational_thread_memory.solo_greenfield_thread_memory import sync_thread_from_solo_greenfield

    sync_thread_from_solo_greenfield(
        session_id=session_id,
        user_text=user_text,
        plan=plan,
        journal=journal,
        execution_status=execution_status,
    )
    return SoloGreenfieldExecutionResult(
        flow=RailwayGreenfieldFlowResult(
            ok=True,
            blocked=False,
            reply=redact_text(reply),
            intent="railway_greenfield_solo_execution_completed",
            preflight_job_id=preflight_job_id,
            artifacts={
                "solo_execution": True,
                "mutation_performed": True,
                "journal": _safe_journal(journal),
                "solo_final_report": build_solo_final_report_payload(
                    full_report=report,
                    plan=plan,
                    journal=journal,
                    env_report=env_report,
                    execution_status=execution_status,
                ),
            },
        ),
        journal=journal,
    )



def _run_solo_phase_loop(
    *,
    journal: dict[str, Any],
    plan: dict[str, Any],
    policy,
    user_text: str,
    max_steps: int = 36,
) -> tuple[dict[str, Any], str, dict[str, str] | None]:
    current = dict(journal)
    for _ in range(max_steps):
        result = run_single_real_mutation_phase(
            journal=current,
            plan=plan,
            policy=policy,
            user_text=user_text,
        )
        current = dict(result.journal or current)
        verification = current.get("runtime_verification") if isinstance(current.get("runtime_verification"), dict) else {}
        if verification.get("verified") or (
            current.get("runtime_verification_performed") and verification.get("ok")
        ):
            return current, "completed", None
        if result.policy_blocked or result.errors:
            code = str((result.errors or ["SOLO_PHASE_BLOCKED"])[0])
            detail = str(result.detail or "")
            if any(token in detail.lower() for token in ("building", "deploying", "initializing", "pending")):
                time.sleep(8)
                continue
            return current, "failed", {
                "code": code,
                "detail": detail or "Solo execution phase blocked.",
                "required_action": "Resolve the blocker and retry the deployment request.",
                "safe_next_command": user_text,
            }
        if result.idempotent_replay and not result.mutation_performed:
            signature = str(result.detail or "")
            if signature and signature == current.get("_solo_last_idempotent_detail"):
                return current, "failed", {
                    "code": "SOLO_IDEMPOTENT_STALL",
                    "detail": "Solo execution stalled on repeated idempotent phase replay.",
                    "required_action": "Clear the stale execution journal or retry with a fresh session.",
                    "safe_next_command": user_text,
                }
            current["_solo_last_idempotent_detail"] = signature
        if result.idempotent_replay and current.get("runtime_verification_performed"):
            return current, "completed", None
    return current, "failed", {
        "code": "SOLO_EXECUTION_STEP_LIMIT",
        "detail": "Solo execution exceeded the governed phase step limit.",
        "required_action": "Check Mission Control execution journal and retry.",
        "safe_next_command": user_text,
    }


def _blocked_flow(
    *,
    code: str,
    detail: str,
    required_action: str = "",
    safe_next_command: str = "",
) -> RailwayGreenfieldFlowResult:
    return RailwayGreenfieldFlowResult(
        ok=False,
        blocked=True,
        blocker_code=code,
        blocker_detail=detail,
        safe_next_command=safe_next_command,
        reply=_compose_solo_blocker_reply(
            {
                "code": code,
                "detail": detail,
                "required_action": required_action,
                "safe_next_command": safe_next_command,
            }
        ),
        intent="railway_greenfield_solo_execution_blocked",
    )


def _compose_solo_blocker_reply(blocker: dict[str, str]) -> str:
    lines = [
        "**Solo execution blocked**",
        "",
        f"- Blocker: `{blocker.get('code')}`",
        f"- Detail: {blocker.get('detail')}",
    ]
    if blocker.get("required_action"):
        lines.extend(["", f"**Required action:** {blocker['required_action']}"])
    if blocker.get("safe_next_command"):
        lines.append(f"**Safe next command:** `{blocker['safe_next_command']}`")
    return "\n".join(lines)


def _safe_journal(journal: dict[str, Any]) -> dict[str, Any]:
    return {
        k: journal.get(k)
        for k in (
            "execution_id",
            "project",
            "environment",
            "service_name",
            "railway_service_id",
            "railway_deployment_id",
            "deployment_url",
            "runtime_verification_performed",
            "state",
        )
    }
