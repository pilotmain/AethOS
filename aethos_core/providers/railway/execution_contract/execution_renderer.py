# SPDX-License-Identifier: Apache-2.0
"""User-facing Railway execution contract renderers."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    EXECUTION_ENABLED,
    EXECUTION_PHASES,
    ROLLBACK_ACTIONS,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    load_railway_execution_enablement_config,
)
from aethos_core.providers.railway.execution_contract.execution_readiness_gate import (
    RailwayExecutionReadinessGate,
)


def render_execution_contract_overview() -> str:
    return "\n".join(
        [
            "# Railway Execution Contract",
            "",
            "Execution enabled:",
            f"- **{str(EXECUTION_ENABLED).lower()}**",
            "",
            "Current capability:",
            "- governed simulation only",
            "",
            "Execution phases:",
            *[f"{idx}. {phase}" for idx, phase in enumerate(EXECUTION_PHASES, start=1)],
            "",
            "Rollback:",
            "- supported by contract",
            "- not yet executable",
            "",
            "Mutation safety:",
            "- idempotency enforced",
            "- execution lock required",
            "- journal persistence enabled",
            "",
            "No Railway mutation has been performed.",
        ]
    )


def render_execution_phases() -> str:
    lines = [
        "# Railway Execution Phases",
        "",
        "Governed mutation phases (contract-defined, not yet live):",
    ]
    for idx, phase in enumerate(EXECUTION_PHASES, start=1):
        lines.append(f"{idx}. **{phase}**")
    lines.extend(
        [
            "",
            "Phase prompts (future):",
            "- `create railway service`",
            "- connect repo binding",
            "- configure env vars (secure credential path only)",
            "- trigger initial deploy",
            "- verify runtime health and logs",
            "",
            f"Execution enabled: **{str(EXECUTION_ENABLED).lower()}**",
            "",
            "No Railway mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def render_connect_source_rollback_contract(contract: Any) -> str:
    lines = [
        "# Railway connect_source Rollback Contract",
        "",
        f"- execution_id: `{getattr(contract, 'execution_id', '—')}`",
        f"- forward_phase: `{getattr(contract, 'forward_phase', '—')}`",
        f"- rollback_phase: `{getattr(contract, 'rollback_phase', '—')}`",
        f"- rollback_action: `{getattr(contract, 'rollback_action', '—')}`",
        f"- repository: `{getattr(contract, 'repository', '—')}`",
        f"- branch: `{getattr(contract, 'branch', '—')}`",
        f"- dry_run_only: **{str(getattr(contract, 'dry_run_only', True)).lower()}**",
        f"- live_rollback_enabled: **{str(getattr(contract, 'live_rollback_enabled', False)).lower()}**",
        f"- eligible_for_dry_run_rollback: **{str(getattr(contract, 'eligible_for_dry_run_rollback', False)).lower()}**",
        f"- forward_live_mutation_recorded: **{str(getattr(contract, 'forward_live_mutation_recorded', False)).lower()}**",
        f"- eligible_for_live_rollback: **{str(getattr(contract, 'eligible_for_live_rollback', False)).lower()}**",
        f"- forward_phase_recorded: **{str(getattr(contract, 'forward_phase_recorded', False)).lower()}**",
        f"- rollback_receipt_recorded: **{str(getattr(contract, 'rollback_receipt_recorded', False)).lower()}**",
        "",
        "Dry-run steps (FIX 110):",
    ]
    for step in getattr(contract, "steps", None) or ():
        lines.append(f"- {step}")
    if getattr(contract, "live_rollback_enabled", False):
        lines.extend(["", "Live rollback (FIX 111):"])
        for action in getattr(contract, "future_live_actions", None) or ():
            lines.append(f"- {action}")
        lines.append("- use `execute railway source binding rollback` when execution_mode=enabled")
    else:
        lines.extend(
            [
                "",
                "Live rollback (FIX 111, disabled by default):",
            ]
        )
        for action in getattr(contract, "future_live_actions", None) or ():
            lines.append(f"- {action} (requires railway_greenfield_disconnect_source_enabled=true)")
    messages = list(getattr(contract, "blocker_messages", None) or [])
    if messages:
        lines.extend(["", "Blockers:"])
        for msg in messages:
            lines.append(f"- {msg}")
    lines.extend(
        [
            "",
            "Not performed by rollback adapters:",
            "- env var writes",
            "- deploy trigger",
        ]
    )
    return "\n".join(lines)


def render_dry_run_connect_source_rollback_result(result: Any) -> str:
    journal = result.journal if hasattr(result, "journal") else {}
    lines = [
        "# Railway connect_source Rollback (Dry Run)",
        "",
        f"- execution_id: `{journal.get('execution_id', '—')}`",
        f"- mutation_performed: **false**",
        f"- idempotent_replay: **{str(getattr(result, 'idempotent_replay', False)).lower()}**",
        f"- rollback_receipt_recorded: **{str(getattr(result, 'rollback_receipt_recorded', False)).lower()}**",
    ]
    if getattr(result, "detail", ""):
        lines.extend(["", str(result.detail)])
    errors = list(getattr(result, "errors", None) or [])
    if errors:
        lines.extend(["", "Errors:"])
        for err in errors:
            lines.append(f"- {err}")
    lines.extend(
        [
            "",
            "Use `show railway rollback timeline` or `show railway rollback receipts` for rollback_connect_source.",
        ]
    )
    return "\n".join(lines)


def render_live_connect_source_rollback_result(result: Any) -> str:
    journal = result.journal if hasattr(result, "journal") else {}
    mutation = getattr(result, "mutation_performed", False)
    lines = [
        "# Railway connect_source Rollback (Live)",
        "",
        f"- execution_id: `{journal.get('execution_id', '—')}`",
        f"- mutation_performed: **{str(mutation).lower()}**",
        f"- idempotent_replay: **{str(getattr(result, 'idempotent_replay', False)).lower()}**",
        f"- rollback_receipt_recorded: **{str(getattr(result, 'rollback_receipt_recorded', False)).lower()}**",
        f"- policy_blocked: **{str(getattr(result, 'policy_blocked', False)).lower()}**",
    ]
    if getattr(result, "detail", ""):
        lines.extend(["", str(result.detail)])
    errors = list(getattr(result, "errors", None) or [])
    if errors:
        lines.extend(["", "Errors:"])
        for err in errors:
            lines.append(f"- {err}")
    lines.extend(
        [
            "",
            "Receipt phase: `rollback_connect_source` (live mutation when mutation_performed=true).",
            "Use `show railway rollback timeline` or `show railway rollback receipts`.",
        ]
    )
    return "\n".join(lines)


def render_rollback_contract() -> str:
    lines = [
        "# Railway Rollback Contract",
        "",
        "Rollback journal is required before any future mutation.",
        "",
        "Rollback actions:",
    ]
    for action in ROLLBACK_ACTIONS:
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "Partial failure semantics:",
            "- never mark `execution_completed` unless all phases succeed",
            "- `execution_partial_failure` keeps `rollback_available: true`",
            "",
            "Rollback phases are journaled; execution remains contract-only today.",
            "",
            "No Railway mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def render_execution_journal(
    journal: dict[str, Any] | None,
    *,
    readiness_gate: RailwayExecutionReadinessGate | None = None,
) -> str:
    if not journal:
        return "\n".join(
            [
                "No Railway execution journal found for this session/target.",
                "",
                "Run `execute railway service creation` after simulation completes.",
                "",
                "No Railway mutation has been performed.",
            ]
        )
    lines = [
        "# Railway Execution Journal",
        "",
        f"- execution_id: `{journal.get('execution_id', '—')}`",
        f"- plan_id: `{journal.get('plan_id', '—')}`",
        f"- state: **{journal.get('state', '—')}**",
        f"- idempotency_key: `{journal.get('idempotency_key', '—')}`",
        f"- mutation_enabled: **{str(journal.get('mutation_enabled', False)).lower()}**",
        f"- rollback_ready: **{str(journal.get('rollback_ready', False)).lower()}**",
        f"- rollback_available: **{str(journal.get('rollback_available', False)).lower()}**",
        f"- repo: `{journal.get('repo', '—')}`",
        f"- target: `{journal.get('project', '—')}` / `{journal.get('environment', '—')}` / `{journal.get('service_name', '—')}`",
    ]
    approval = journal.get("approval") or {}
    if approval:
        lines.append("")
        lines.append("Approval gates:")
        for key in (
            "review_confirmed",
            "preflight_approved",
            "mutation_ready",
            "simulation_complete",
            "execution_enabled",
            "ready_to_execute",
        ):
            if key in approval:
                lines.append(f"- {key}: **{approval[key]}**")
    phases = list(journal.get("phases") or [])
    if phases:
        lines.append("")
        lines.append("Recorded phases:")
        for row in phases:
            lines.append(f"- {row.get('phase')}: {row.get('status')}")
    if readiness_gate is not None:
        lines.extend(
            [
                "",
                "Execution readiness:",
                f"- ready_to_execute: **{str(readiness_gate.ready).lower()}**",
                f"- blocking checks: **{readiness_gate.blocking_count()}**",
            ]
        )
    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)


def render_execution_receipts(receipts: list[dict[str, Any]], *, execution_id: str = "") -> str:
    lines = ["# Railway Execution Receipts", ""]
    if execution_id:
        lines.append(f"- execution_id: `{execution_id}`")
        lines.append("")
    if not receipts:
        lines.extend(
            [
                "No execution receipts recorded yet.",
                "",
                "No Railway mutation has been performed.",
            ]
        )
        return "\n".join(lines)
    for idx, receipt in enumerate(receipts, start=1):
        lines.extend(
            [
                "",
                "Receipt:",
                f"- phase: `{receipt.get('phase', '—')}`",
                f"- status: **{receipt.get('status', '—')}**",
                f"- replayed: **{str(receipt.get('replayed', False)).lower()}**",
                f"- mutation_performed: **{str(receipt.get('mutation_performed', False)).lower()}**",
            ]
        )
        if receipt.get("skipped_existing"):
            lines.append(f"- skipped_existing: **true**")
        duration = receipt.get("duration_ms")
        if duration is not None:
            lines.append(f"- duration_ms: {duration}")
        lines.append(f"- started_at: {receipt.get('started_at', receipt.get('timestamp', '—'))}")
        lines.append(f"- completed_at: {receipt.get('completed_at', '—')}")
    if _live_mutation_occurred(None, receipts):
        lines.extend(["", "Live Railway mutation receipts are present for this execution."])
    else:
        lines.extend(["", "No live Railway mutation has been performed."])
    return "\n".join(lines)


def render_rollback_timeline(
    journal: dict[str, Any] | None,
    *,
    receipts: list[dict[str, Any]] | None = None,
) -> str:
    if not journal:
        return "\n".join(
            [
                "# Railway Rollback Timeline",
                "",
                "No execution journal found for this session/target.",
                "",
                "No Railway mutation has been performed.",
            ]
        )
    from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
        DISABLE_DEPLOYS_ROLLBACK_PHASE,
        REMOVE_SERVICE_ROLLBACK_PHASE,
        REVERT_ENV_ROLLBACK_PHASE,
        CONNECT_SOURCE_ROLLBACK_PHASE,
    )

    execution_id = str(journal.get("execution_id") or "—")
    rollback_rows = [
        r
        for r in list(receipts or [])
        if str(r.get("phase") or "").startswith("rollback_")
    ]
    by_phase = {str(r.get("phase") or ""): r for r in rollback_rows}
    ordered = [
        (CONNECT_SOURCE_ROLLBACK_PHASE, "disconnect_repo_source"),
        (REVERT_ENV_ROLLBACK_PHASE, "revert_env_writes"),
        (DISABLE_DEPLOYS_ROLLBACK_PHASE, "disable_deploys"),
        (REMOVE_SERVICE_ROLLBACK_PHASE, "remove_created_service"),
    ]
    lines = [
        "# Railway Rollback Timeline",
        "",
        f"- execution_id: `{execution_id}`",
        f"- rollback_completed: **{str(journal.get('rollback_completed', False)).lower()}**",
        "",
    ]
    for idx, (phase, label) in enumerate(ordered, start=1):
        receipt = by_phase.get(phase)
        if receipt:
            status = receipt.get("status", "—")
            lines.append(f"{idx}. {label}")
            lines.append(f"   - {status}")
        else:
            lines.append(f"{idx}. {label}")
            lines.append("   - (not recorded)")
    extra = [r for r in rollback_rows if str(r.get("phase") or "") not in {p for p, _ in ordered}]
    if extra:
        lines.append("")
        lines.append("Additional rollback receipts:")
        for receipt in extra:
            lines.append(f"- {receipt.get('phase')}: {receipt.get('status')}")
    any_live_mutation = any(bool(r.get("mutation_performed")) for r in rollback_rows)
    lines.extend(
        [
            "",
            "Readonly audit view — secret values are never shown.",
        ]
    )
    if not any_live_mutation:
        lines.append("No live rollback mutation receipts with mutation_performed=true in this view.")
    return "\n".join(lines)


def render_rollback_readiness(readiness: Any) -> str:
    lines = [
        "# Railway Rollback Readiness",
        "",
        f"- ready_for_live_rollback: **{str(getattr(readiness, 'ready_for_live_rollback', False)).lower()}**",
        "",
        "Rollback checks:",
        f"- staging_only: **{str(getattr(readiness, 'staging_only', False)).lower()}**",
        f"- live_forward_execution_exists: **{str(getattr(readiness, 'live_forward_execution_exists', False)).lower()}**",
        f"- rollback_contract_present: **{str(getattr(readiness, 'rollback_contract_present', False)).lower()}**",
        f"- rollback_lock_available: **{str(getattr(readiness, 'rollback_lock_available', False)).lower()}**",
        f"- disconnect_source_enabled: **{str(getattr(readiness, 'disconnect_source_enabled', False)).lower()}**",
        f"- revert_env_enabled: **{str(getattr(readiness, 'revert_env_enabled', False)).lower()}**",
        f"- production_target: **{str(getattr(readiness, 'production_target', False)).lower()}**",
        "",
        "Rollback phases available:",
    ]
    phases = list(getattr(readiness, "phases_available", None) or [])
    if phases:
        for phase in phases:
            lines.append(f"- {phase}")
    else:
        lines.append("- (none)")
    lines.extend(["", "Rollback phases simulated only:"])
    simulated = list(getattr(readiness, "phases_simulated_only", None) or [])
    for phase in simulated:
        lines.append(f"- {phase}")
    messages = list(getattr(readiness, "messages", None) or [])
    if messages:
        lines.extend(["", "Notes:"])
        for msg in messages:
            lines.append(f"- {msg}")
    blockers = list(getattr(readiness, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    lines.extend(
        [
            "",
            "No rollback executed.",
            "No mutation performed.",
        ]
    )
    return "\n".join(lines)


def render_live_rollback_result(result: Any) -> str:
    journal = result.journal if hasattr(result, "journal") else {}
    lines = [
        "# Railway Live Rollback",
        "",
        f"- execution_id: `{journal.get('execution_id', '—')}`",
        f"- mutation_performed: **{str(getattr(result, 'mutation_performed', False)).lower()}**",
        f"- rollback_completed: **{str(getattr(result, 'rollback_completed', False)).lower()}**",
        f"- partial_failure: **{str(getattr(result, 'partial_failure', False)).lower()}**",
        f"- policy_blocked: **{str(getattr(result, 'policy_blocked', False)).lower()}**",
    ]
    if getattr(result, "detail", ""):
        lines.extend(["", str(result.detail)])
    errors = list(getattr(result, "errors", None) or [])
    if errors:
        lines.extend(["", "Errors:"])
        for err in errors:
            lines.append(f"- {err}")
    lines.extend(
        [
            "",
            "Use `show railway rollback timeline` for receipt-ordered rollback evidence.",
        ]
    )
    return "\n".join(lines)


def render_rollback_receipts(receipts: list[dict[str, Any]], *, execution_id: str = "") -> str:
    rollback_rows = [r for r in receipts if str(r.get("phase") or "").startswith("rollback_")]
    lines = ["# Railway Rollback Receipts", ""]
    if execution_id:
        lines.append(f"- execution_id: `{execution_id}`")
        lines.append("")
    if not rollback_rows:
        lines.extend(
            [
                "No rollback receipts recorded yet.",
                "",
                "No Railway mutation has been performed.",
            ]
        )
        return "\n".join(lines)
    for receipt in rollback_rows:
        lines.extend(
            [
                "",
                "Receipt:",
                f"- phase: `{receipt.get('phase', '—')}`",
                f"- status: **{receipt.get('status', '—')}**",
                f"- replayed: **{str(receipt.get('replayed', False)).lower()}**",
                f"- mutation_performed: **{str(receipt.get('mutation_performed', False)).lower()}**",
            ]
        )
    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)


def render_execution_timeline(
    journal: dict[str, Any] | None,
    *,
    receipts: list[dict[str, Any]] | None = None,
) -> str:
    if not journal:
        return "\n".join(
            [
                "# Railway Execution Timeline",
                "",
                "No execution journal found for this session/target.",
                "",
                "No Railway mutation has been performed.",
            ]
        )
    execution_id = str(journal.get("execution_id") or "—")
    mode = str(journal.get("execution_mode") or "disabled")
    rows = list(receipts or [])
    phase_receipts = [
        r for r in rows if str(r.get("phase") or "") in EXECUTION_PHASES
    ]
    rollback_receipts = [r for r in rows if str(r.get("phase") or "").startswith("rollback_")]
    state = str(journal.get("state") or "")
    lines = [
        "# Railway Execution Timeline",
        "",
        "Execution:",
        f"- execution_id: `{execution_id}`",
        f"- state: **{state or '—'}**",
        "",
        "Mode:",
        f"- **{mode}**",
        "",
        "Timeline:",
    ]
    if not phase_receipts:
        lines.append("- (no phase receipts recorded)")
    else:
        for idx, receipt in enumerate(phase_receipts, start=1):
            phase = receipt.get("phase", "—")
            status = receipt.get("status", "—")
            lines.append(f"{idx}. {phase} — {status}")
    if state == "execution_partial_failure":
        failure_phase = str(journal.get("dry_run_failure_phase") or "—")
        lines.extend(
            [
                "",
                "Partial failure:",
                f"- failed at phase: `{failure_phase}`",
                f"- rollback_available: **{str(journal.get('rollback_available', False)).lower()}**",
                "- remaining phases were not executed",
            ]
        )
    if rollback_receipts:
        lines.extend(["", "Rollback (simulated):"])
        for idx, receipt in enumerate(rollback_receipts, start=1):
            lines.append(f"{idx}. {receipt.get('phase', '—')} — {receipt.get('status', '—')}")
    if _live_mutation_occurred(journal, rows):
        lines.extend(
            [
                "",
                "Mutation performed:",
                "- true (live create_service receipt recorded)",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Mutation performed:",
                "- false",
                "",
                "No live Railway mutation has been performed.",
            ]
        )
    return "\n".join(lines)


def render_execution_request_result(result: dict[str, Any]) -> str:
    journal = result.get("journal") or {}
    mutation_performed = bool(result.get("mutation_performed"))
    real_result = result.get("real_mutation_result")
    if real_result is not None:
        mutation_performed = bool(getattr(real_result, "mutation_performed", mutation_performed))
    lines = [
        "# Railway Execution Request",
        "",
        f"- execution_id: `{journal.get('execution_id', '—')}`",
        f"- state: **{journal.get('state', '—')}**",
        f"- journal_created: **{str(result.get('journal_created', False)).lower()}**",
        f"- lock_acquired: **{str(result.get('lock_acquired', False)).lower()}**",
        f"- execution_mode: **{journal.get('execution_mode', '—')}**",
        f"- mutation_performed: **{str(mutation_performed).lower()}**",
    ]
    if journal.get("railway_service_id"):
        lines.append(f"- railway_service_id: `{journal.get('railway_service_id')}`")
    if result.get("approval_blockers"):
        lines.append("")
        lines.append("Blocked until:")
        for blocker in result["approval_blockers"]:
            lines.append(f"- {blocker}")
    if result.get("detail"):
        lines.append("")
        lines.append(str(result["detail"]))
    real_mutation_result = result.get("real_mutation_result")
    if real_mutation_result is not None and getattr(real_mutation_result, "executed_phases", None):
        lines.append("")
        lines.append("Real mutation phases executed this run:")
        for phase in real_mutation_result.executed_phases:
            lines.append(f"- {phase}")
    if real_mutation_result is not None and getattr(real_mutation_result, "idempotent_replay", False):
        lines.append("")
        lines.append("Idempotent replay: create_service was not re-invoked.")
    dry_run_result = result.get("dry_run_result")
    if dry_run_result is not None and getattr(dry_run_result, "executed_phases", None):
        lines.append("")
        lines.append("Phases executed this run:")
        for phase in dry_run_result.executed_phases:
            lines.append(f"- {phase}")
    if dry_run_result is not None and getattr(dry_run_result, "skipped_phases", None):
        lines.append("")
        lines.append("Phases skipped (already simulated):")
        for phase in dry_run_result.skipped_phases:
            lines.append(f"- {phase}")
    if dry_run_result is not None and getattr(dry_run_result, "partial_failure", False):
        lines.append("")
        lines.append("Partial failure:")
        lines.append(f"- failed at phase: `{getattr(dry_run_result, 'failure_phase', '')}`")
        lines.append("- rollback receipts recorded (simulated)")
        lines.append("- use `show railway rollback timeline` or `show railway rollback receipts`")
    if str(journal.get("state") or "") == "execution_partial_failure" and not (
        dry_run_result and getattr(dry_run_result, "executed_phases", None)
    ):
        lines.append("")
        lines.append("Execution is already in partial_failure for this target.")
        lines.append("Re-run is idempotent — no additional phases or rollback receipts were added.")
    if result.get("lock_reason"):
        lines.append("")
        lines.append(f"Lock: {result['lock_reason']}")
    lines.extend(
        [
            "",
            "Contract actions recorded:",
            "- execution journal persisted",
            "- rollback journal prepared",
            "- simulated phase receipts written",
            "",
            "No Railway mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def render_railway_production_policy(assessment: Any) -> str:
    """FIX 117 — production governance policy report (no mutations)."""
    lines = [
        "# Railway Production Policy",
        "",
        "Environment:",
        f"- tier: **{getattr(assessment, 'environment_tier', '—')}**",
        f"- blast radius: **{getattr(assessment, 'blast_radius', '—')}**",
        f"- mutation risk: **{getattr(assessment, 'mutation_risk_tier', '—')}**",
        "",
        "Operational modes:",
        f"- incident mode: **{str(getattr(assessment, 'incident_mode_active', False)).lower()}**",
        f"- deployment freeze: **{str(getattr(assessment, 'deployment_freeze_active', False)).lower()}**",
        f"- shadow mode required (production): **{str(getattr(assessment, 'shadow_mode_required', False)).lower()}**",
        f"- rollout mode: **{getattr(assessment, 'rollout_mode', '—')}**",
        "",
        "Execution gates:",
        f"- forward live permitted: **{str(getattr(assessment, 'forward_live_permitted', False)).lower()}**",
        f"- rollback permitted: **{str(getattr(assessment, 'rollback_permitted', False)).lower()}**",
        f"- rollback escalation: **{getattr(assessment, 'rollback_escalation', 'manual_only')}**",
        f"- autonomous rollback blocked: **{str(getattr(assessment, 'autonomous_rollback_blocked', True)).lower()}**",
        "",
        "Approvals:",
        f"- production phrase valid (this message): **{str(getattr(assessment, 'production_phrase_valid', False)).lower()}**",
        f"- quorum confirmation valid (this message): **{str(getattr(assessment, 'quorum_confirmation_valid', False)).lower()}**",
        f"- operator quorum satisfied: **{str(getattr(assessment, 'operator_quorum_satisfied', False)).lower()}**",
        f"- quorum recorded / required: {getattr(assessment, 'quorum_confirmations_recorded', 0)} / {getattr(assessment, 'quorum_required', 0)}",
        "",
        "Verification & audit:",
        f"- SLO verification required: **{str(getattr(assessment, 'slo_verification_required', False)).lower()}**",
        f"- SLO verification satisfied: **{str(getattr(assessment, 'slo_verification_satisfied', False)).lower()}**",
        f"- audit retention (days): **{getattr(assessment, 'audit_retention_days', 90)}**",
    ]
    blockers = getattr(assessment, "blockers", None) or []
    messages = getattr(assessment, "messages", None) or []
    if messages:
        lines.extend(["", "Policy messages:"])
        for msg in messages:
            lines.append(f"- {msg}")
    if blockers:
        lines.extend(["", "Blocker codes:"])
        for code in blockers:
            lines.append(f"- `{code}`")
    lines.extend(
        [
            "",
            "Production live forward execution remains locked until explicitly unlocked, "
            "quorum is recorded, and SLO verification passes.",
            "",
            "No Railway mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def render_railway_execution_enablement(
    policy: RailwayExecutionEnablementPolicy,
) -> str:
    cfg = load_railway_execution_enablement_config()
    projects = ", ".join(cfg.allowed_projects) or "—"
    environments = ", ".join(cfg.allowed_environments) or "—"
    services = ", ".join(cfg.allowed_services) or "(any)"
    lines = [
        "# Railway Execution Enablement",
        "",
        "Mode:",
        f"- **{policy.mode}**",
        "",
        "Runtime policy:",
        f"- greenfield execution enabled: **{str(policy.greenfield_execution_enabled).lower()}**",
        f"- allowed projects: {projects}",
        f"- allowed environments: {environments}",
        f"- production allowed: **{str(policy.production_allowed).lower()}**",
        f"- final phrase required: **{str(policy.final_phrase_required).lower()}**",
    ]
    if cfg.allowed_services:
        lines.append(f"- allowed services: {services}")
    lines.extend(["", "Current target:"])
    if not policy.target_loaded:
        lines.append("- none loaded")
    else:
        lines.extend(
            [
                f"- project: {policy.target_project}",
                f"- environment: {policy.target_environment}",
                f"- service: {policy.target_service or '—'}",
            ]
        )
    lines.extend(
        [
            "",
            "Policy result:",
            f"- allowed: **{str(policy.allowed).lower()}**",
        ]
    )
    if policy.blocking_reason_messages:
        lines.extend(["", "Blocking reasons:"])
        for reason in policy.blocking_reason_messages:
            lines.append(f"- {reason}")
    if policy.next_step:
        lines.extend(["", "Next step:", policy.next_step])
    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)


def render_execution_readiness_gate(gate: RailwayExecutionReadinessGate) -> str:
    """Authoritative execution readiness gate report."""
    matrix = gate.display_gate_matrix()
    lines = [
        "# Railway Execution Readiness Gate",
        "",
        f"ready_to_execute: **{str(gate.ready).lower()}**",
        "",
        "Gate checks:",
        f"- deployment plan: {matrix.get('deployment_plan', '—')}",
        f"- review confirmed: {matrix.get('review_confirmed', '—')}",
        f"- preflight exists: {matrix.get('preflight_created', '—')}",
        f"- preflight approved: {matrix.get('preflight_approved', '—')}",
        f"- simulation exists: {matrix.get('simulation_complete', '—')}",
        f"- simulation ready: {matrix.get('simulation_ready_to_execute', '—')}",
        f"- env readiness: {matrix.get('env_readiness', '—')}",
        f"- execution lock available: {matrix.get('execution_lock_available', '—')}",
        f"- execution policy: {matrix.get('execution_policy', '—')}",
        f"- execution mode: {matrix.get('execution_mode', '—')}",
        f"- phase execution allowed: {matrix.get('phase_execution_allowed', '—')}",
        f"- real mutation allowed: {matrix.get('real_mutation_allowed', '—')}",
        f"- execution enabled: {matrix.get('execution_enabled', '—')}",
    ]
    if gate.checks.get("mutation_ready") is not None:
        lines.append(
            f"- mutation ready: {'pass' if gate.checks.get('mutation_ready') == 'pass' else 'fail'}"
        )
    if gate.checks.get("critical_env_secrets_configured") is not None:
        lines.append(
            "- critical env secrets configured: "
            f"{matrix.get('critical_env_secrets_detail', '—')}"
        )
        lines.append(f"- env readiness confidence: {matrix.get('env_readiness_confidence', '—')}")
        lines.append(
            f"- minimum secret set: {matrix.get('minimum_secret_set_complete', '—')}"
        )
    if gate.checks.get("execution_contract_exists") is not None:
        lines.append(
            f"- execution contract: {matrix.get('execution_contract_exists', '—')}"
        )

    messages = list(gate.blocking_reason_messages)
    if messages:
        lines.extend(["", "Blocking reasons:"])
        for reason in messages:
            lines.append(f"- {reason}")

    if gate.phase_execution_allowed and not gate.real_mutation_allowed:
        lines.extend(
            [
                "",
                "Note: dry-run phase execution is allowed. Real Railway mutation remains disabled.",
            ]
        )
    elif not gate.execution_enabled:
        lines.extend(
            [
                "",
                "Note: approving preflight or completing simulation only advances readiness state; "
                "it does not execute Railway service creation while execution is disabled.",
            ]
        )

    if gate.next_steps:
        lines.extend(["", "Next steps:"])
        for idx, step in enumerate(gate.next_steps, start=1):
            lines.append(f"{idx}. `{step}`")

    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)


def render_execution_request_blockers(assessment: dict[str, Any]) -> str:
    """Detailed execution gate matrix, blocking reasons, and next steps."""
    matrix = dict(assessment.get("gate_matrix") or {})
    lines = [
        "Cannot request Railway service creation execution yet.",
        "",
        "Execution gate:",
        f"- deployment plan: {matrix.get('deployment_plan', '—')}",
        f"- review confirmed: {matrix.get('review_confirmed', '—')}",
        f"- preflight created: {matrix.get('preflight_created', '—')}",
        f"- preflight approved: {matrix.get('preflight_approved', '—')}",
        f"- simulation complete: {matrix.get('simulation_complete', '—')}",
        f"- simulation ready_to_execute: {matrix.get('simulation_ready_to_execute', '—')}",
        f"- env readiness: {matrix.get('env_readiness', '—')}",
        f"- execution enabled: {matrix.get('execution_enabled', '—')}",
    ]

    reasons = list(assessment.get("blocking_reasons") or [])
    if reasons:
        lines.extend(["", "Blocking reasons:"])
        for reason in reasons:
            lines.append(f"- {reason}")

    if matrix.get("execution_enabled") == "no":
        lines.extend(
            [
                "",
                "Note: approving preflight or completing simulation only advances readiness state; "
                "it does not execute Railway service creation while execution is disabled.",
            ]
        )

    steps = list(assessment.get("next_steps") or [])
    if steps:
        lines.extend(["", "Next steps:"])
        for idx, step in enumerate(steps, start=1):
            lines.append(f"{idx}. `{step}`")

    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)


def _live_mutation_occurred(
    journal: dict[str, Any] | None,
    receipts: list[dict[str, Any]] | None,
) -> bool:
    if journal and str(journal.get("railway_service_id") or "").strip():
        return True
    from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
        receipt_is_live_mutation,
    )

    for receipt in receipts or []:
        if receipt_is_live_mutation(receipt):
            return True
    return False


def render_mutation_preview(preview: Any) -> str:
    lines = [
        "# Railway Mutation Preview",
        "",
        "What would mutate (read-only):",
        f"- operation: `{getattr(preview, 'operation', '—')}`",
        f"- would_mutate: **{str(getattr(preview, 'would_mutate', False)).lower()}**",
        f"- project: `{getattr(preview, 'project_name', '—')}`",
        f"- environment: `{getattr(preview, 'environment_name', '—')}`",
        f"- service: `{getattr(preview, 'service_name', '—')}`",
        f"- execution_mode: **{getattr(preview, 'execution_mode', '—')}**",
        f"- kill_switch_active: **{str(getattr(preview, 'kill_switch_active', False)).lower()}**",
    ]
    if getattr(preview, "resolved_project_id", ""):
        lines.append(f"- resolved_project_id: `{preview.resolved_project_id}`")
    if getattr(preview, "resolved_environment_id", ""):
        lines.append(f"- resolved_environment_id: `{preview.resolved_environment_id}`")
    if getattr(preview, "idempotent_replay", False):
        lines.append("- idempotent_replay: **true** (no duplicate serviceCreate)")
    if getattr(preview, "service_already_exists", False):
        lines.append("- service_already_exists: **true**")
    blockers = list(getattr(preview, "blocker_messages", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for msg in blockers:
            lines.append(f"- {msg}")
    lines.extend(
        [
            "",
            "Not performed (unless this phase is connect_source):",
            "- env var writes",
            "- deploy trigger",
            "- runtime verification",
        ]
    )
    return "\n".join(lines)


def render_mutation_audit(report: Any) -> str:
    lines = [
        "# Railway Live Mutation Audit",
        "",
        f"- audit_ok: **{str(getattr(report, 'ok', False)).lower()}**",
        f"- kill_switch_active: **{str(getattr(report, 'kill_switch_active', False)).lower()}**",
        f"- execution_mode: **{getattr(report, 'execution_mode', '—')}**",
        f"- dry_run isolated from live adapter: **{str(getattr(report, 'dry_run_cannot_reach_live_adapter', False)).lower()}**",
        f"- live adapter requires enabled mode: **{str(getattr(report, 'live_adapter_requires_enabled_mode', False)).lower()}**",
        f"- live adapter requires authorization gate: **{str(getattr(report, 'live_adapter_requires_authorization_token', False)).lower()}**",
        f"- preview_would_mutate: **{str(getattr(report, 'preview_would_mutate', False)).lower()}**",
        f"- idempotent_replay_would_skip: **{str(getattr(report, 'idempotent_replay_would_skip', False)).lower()}**",
        "",
        "Isolation checks:",
    ]
    for check in getattr(report, "isolation_checks", None) or []:
        mark = "pass" if check.passed else "fail"
        lines.append(f"- {check.name}: **{mark}** — {check.detail}")
    summary = getattr(report, "receipt_summary", None) or {}
    lines.append("")
    lines.append("Receipt status summary:")
    if not summary:
        lines.append("- (no receipts for this execution)")
    else:
        for status, count in sorted(summary.items()):
            lines.append(f"- {status}: {count}")
    lines.append("")
    lines.append(
        f"- live mutation receipts: {getattr(report, 'live_mutation_receipt_count', 0)}"
    )
    lines.append(
        f"- simulated receipts: {getattr(report, 'simulated_receipt_count', 0)}"
    )
    blockers = list(getattr(report, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Runtime blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    return "\n".join(lines)


def render_source_binding_status(status: Any) -> str:
    lines = [
        "# Railway Source Binding Status",
        "",
        f"- binding_recorded_on_journal: **{str(getattr(status, 'binding_recorded_on_journal', False)).lower()}**",
        f"- journal_repository: `{getattr(status, 'journal_repository', '—')}`",
        f"- journal_branch: `{getattr(status, 'journal_branch', '—')}`",
        f"- service_id: `{getattr(status, 'service_id', '—')}`",
        f"- environment_id: `{getattr(status, 'environment_id', '—')}`",
        f"- connect_source_receipt_status: **{getattr(status, 'connect_source_receipt_status', '—')}**",
        f"- mutation_performed: **{str(getattr(status, 'mutation_performed', False)).lower()}**",
        f"- idempotent_replay: **{str(getattr(status, 'idempotent_replay', False)).lower()}**",
        f"- skip_deploys_enforced: **{str(getattr(status, 'skip_deploys_enforced', False)).lower()}**",
        f"- ready_for_env_writes: **{str(getattr(status, 'ready_for_env_writes', False)).lower()}**",
        f"- rollback_plan_available: **{str(getattr(status, 'rollback_plan_available', False)).lower()}**",
    ]
    verification = getattr(status, "readonly_verification", None)
    if verification is not None:
        lines.extend(
            [
                "",
                "Read-only verification:",
                f"- verified: **{str(getattr(verification, 'verified', False)).lower()}**",
                f"- repository_observed: `{getattr(verification, 'repository_observed', '—')}`",
                f"- branch_observed: `{getattr(verification, 'branch_observed', '—')}`",
                f"- detail: {getattr(verification, 'detail', '—')}",
            ]
        )
    messages = list(getattr(status, "messages", None) or [])
    if messages:
        lines.extend(["", "Notes:"])
        for msg in messages:
            lines.append(f"- {msg}")
    blockers = list(getattr(status, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    lines.extend(
        [
            "",
            "Not performed by this phase:",
            "- env var writes (FIX 112)",
            "- deploy trigger (FIX 113)",
        ]
    )
    return "\n".join(lines)


def render_source_binding_audit(report: Any) -> str:
    lines = [
        "# Railway Source Binding Audit",
        "",
        f"- audit_ok: **{str(getattr(report, 'ok', False)).lower()}**",
        f"- skip_deploys_enforced_in_code: **{str(getattr(report, 'skip_deploys_enforced_in_code', False)).lower()}**",
        f"- stage_input_source_only_guard: **{str(getattr(report, 'stage_input_source_only_guard', False)).lower()}**",
        f"- no_env_writes_in_adapter: **{str(getattr(report, 'no_env_write_paths_in_adapter', False)).lower()}**",
        f"- no_deploy_trigger_in_adapter: **{str(getattr(report, 'no_deploy_trigger_in_adapter', False)).lower()}**",
        f"- idempotent_replay_would_skip: **{str(getattr(report, 'idempotent_replay_would_skip', False)).lower()}**",
    ]
    receipt = getattr(report, "connect_source_receipt", None)
    if receipt is not None:
        lines.extend(
            [
                "",
                "connect_source receipt:",
                f"- found: **{str(getattr(receipt, 'receipt_found', False)).lower()}**",
                f"- status: **{getattr(receipt, 'status', '—')}**",
                f"- mutation_performed: **{str(getattr(receipt, 'mutation_performed', False)).lower()}**",
                f"- is_simulated: **{str(getattr(receipt, 'is_simulated', False)).lower()}**",
                f"- detail_mentions_skip_deploys: **{str(getattr(receipt, 'detail_mentions_skip_deploys', False)).lower()}**",
                f"- receipt_audit_ok: **{str(getattr(receipt, 'ok', False)).lower()}**",
            ]
        )
    forbidden = list(getattr(report, "forbidden_forward_phases_with_live_mutation", None) or [])
    if forbidden:
        lines.extend(["", "Unexpected live forward phases:"])
        for phase in forbidden:
            lines.append(f"- {phase}")
    verification = getattr(report, "verification", None)
    if verification is not None:
        lines.extend(
            [
                "",
                "Read-only binding verification:",
                f"- verified: **{str(getattr(verification, 'verified', False)).lower()}**",
                f"- repository_expected: `{getattr(verification, 'repository_expected', '—')}`",
                f"- repository_observed: `{getattr(verification, 'repository_observed', '—')}`",
            ]
        )
    rollback = getattr(report, "rollback_plan", None)
    if rollback is not None:
        lines.extend(
            [
                "",
                "Rollback plan (connect_source):",
                f"- action: `{getattr(rollback, 'rollback_action', '—')}`",
                f"- executable: **{str(getattr(rollback, 'executable', False)).lower()}**",
            ]
        )
        for step in getattr(rollback, "steps", None) or []:
            lines.append(f"- {step}")
    blockers = list(getattr(report, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    return "\n".join(lines)


def render_env_configure_rollback_contract(contract: Any) -> str:
    lines = [
        "# Railway configure_env Rollback Contract",
        "",
        f"- execution_id: `{getattr(contract, 'execution_id', '—')}`",
        f"- rollback_action: `{getattr(contract, 'rollback_action', '—')}`",
        f"- rollback_plan_ready: **{str(getattr(contract, 'rollback_plan_ready', False)).lower()}**",
        f"- ready_for_env_writes: **{str(getattr(contract, 'ready_for_env_writes', False)).lower()}**",
        f"- forward_create_service_recorded: **{str(getattr(contract, 'forward_create_service_recorded', False)).lower()}**",
        f"- forward_connect_source_live_recorded: **{str(getattr(contract, 'forward_connect_source_live_recorded', False)).lower()}**",
        "",
        "Groups (receipt per group, never per secret value):",
    ]
    for row in getattr(contract, "groups", None) or ():
        if isinstance(row, dict):
            lines.append(f"- `{row.get('group_id', '—')}`: {', '.join(row.get('env_names') or [])}")
        else:
            gid, names = row
            lines.append(f"- `{gid}`: {', '.join(names)}")
    messages = list(getattr(contract, "blocker_messages", None) or [])
    if messages:
        lines.extend(["", "Notes:"])
        for msg in messages:
            lines.append(f"- {msg}")
    lines.extend(
        [
            "",
            "Not performed:",
            "- deploy trigger",
            "- printing secret values",
        ]
    )
    return "\n".join(lines)


def render_env_configure_status(status: Any) -> str:
    lines = [
        "# Railway Env Configure Status",
        "",
        f"- execution_id: `{getattr(status, 'execution_id', '—')}`",
        f"- configure_env_enabled: **{str(getattr(status, 'configure_env_enabled', False)).lower()}**",
        f"- rollback_plan_ready: **{str(getattr(status, 'rollback_plan_ready', False)).lower()}**",
        f"- rollback_contract_visible: **{str(getattr(status, 'rollback_contract_visible', False)).lower()}**",
        f"- ready_for_env_writes: **{str(getattr(status, 'ready_for_env_writes', False)).lower()}**",
        f"- env_names_verified: **{str(getattr(status, 'env_names_verified', False)).lower()}**",
        f"- ready_for_deploy_trigger: **{str(getattr(status, 'ready_for_deploy_trigger', False)).lower()}**",
        f"- groups_recorded: **{getattr(status, 'groups_recorded', 0)}**",
        f"- group_receipt_count: **{getattr(status, 'group_receipt_count', 0)}**",
        f"- skip_deploys_enforced: **{str(getattr(status, 'skip_deploys_enforced', False)).lower()}**",
    ]
    verification = getattr(status, "readonly_verification", None)
    if verification is not None:
        lines.extend(
            [
                "",
                "Read-only env verification (names only):",
                f"- verified: **{str(getattr(verification, 'verified', False)).lower()}**",
                f"- minimum_secrets_present: **{str(getattr(verification, 'minimum_secrets_present', False)).lower()}**",
                f"- names_observed: `{', '.join(getattr(verification, 'names_observed', ()) or ()) or '—'}`",
                f"- missing_names: `{', '.join(getattr(verification, 'missing_names', ()) or ()) or '—'}`",
            ]
        )
    deploy = getattr(status, "deploy_trigger_readiness", None)
    if deploy is not None:
        lines.extend(
            [
                "",
                "FIX 113 deploy trigger prerequisites:",
                f"- create_service_live_success: **{str(getattr(deploy, 'create_service_live_success', False)).lower()}**",
                f"- connect_source_live_success: **{str(getattr(deploy, 'connect_source_live_success', False)).lower()}**",
                f"- configure_env_live_success: **{str(getattr(deploy, 'configure_env_live_success', False)).lower()}**",
                f"- deploy_trigger_enabled: **{str(getattr(deploy, 'deploy_trigger_enabled', False)).lower()}**",
            ]
        )
    messages = list(getattr(status, "messages", None) or [])
    if messages:
        lines.extend(["", "Notes:"])
        for msg in messages:
            lines.append(f"- {msg}")
    blockers = list(getattr(status, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    lines.extend(
        [
            "",
            "Security:",
            "- values are resolved from secure store only",
            "- no secret values are printed in status or receipts",
        ]
    )
    return "\n".join(lines)


def render_env_configure_verification(verification: Any) -> str:
    lines = [
        "# Railway Env Configure Verification (Read-Only)",
        "",
        f"- verified: **{str(getattr(verification, 'verified', False)).lower()}**",
        f"- minimum_secrets_present: **{str(getattr(verification, 'minimum_secrets_present', False)).lower()}**",
        f"- required: `{', '.join(getattr(verification, 'minimum_secret_names_required', ()) or ()) or '—'}`",
        f"- observed: `{', '.join(getattr(verification, 'names_observed', ()) or ()) or '—'}`",
        f"- missing: `{', '.join(getattr(verification, 'missing_names', ()) or ()) or '—'}`",
        "",
        "Secret values are never read or displayed.",
    ]
    if getattr(verification, "detail", ""):
        lines.extend(["", str(verification.detail)])
    return "\n".join(lines)


def render_deploy_trigger_rollback_contract(contract: Any) -> str:
    lines = [
        "# Railway Deploy Trigger Rollback Contract",
        "",
        f"- execution_id: `{getattr(contract, 'execution_id', '—')}`",
        f"- rollback_action: `{getattr(contract, 'rollback_action', '—')}`",
        f"- rollback_plan_ready: **{str(getattr(contract, 'rollback_plan_ready', False)).lower()}**",
        f"- ready_for_deploy_trigger: **{str(getattr(contract, 'ready_for_deploy_trigger', False)).lower()}**",
        f"- deploy_trigger_enabled: **{str(getattr(contract, 'deploy_trigger_enabled', False)).lower()}**",
        f"- rollback_journal_present: **{str(getattr(contract, 'rollback_journal_present', False)).lower()}**",
    ]
    messages = list(getattr(contract, "blocker_messages", None) or [])
    if messages:
        lines.extend(["", "Notes:"])
        for msg in messages:
            lines.append(f"- {msg}")
    blockers = list(getattr(contract, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    lines.extend(
        [
            "",
            "Not performed:",
            "- runtime verification (FIX 114)",
            "- production deploy",
            "- auto-promotion",
        ]
    )
    return "\n".join(lines)


def render_live_trigger_deploy_result(result: Any) -> str:
    journal = result.journal if hasattr(result, "journal") else {}
    metadata = journal.get("deploy_trigger_metadata") if isinstance(journal.get("deploy_trigger_metadata"), dict) else {}
    lines = [
        "# Railway Deploy Trigger (Live)",
        "",
        f"- execution_id: `{journal.get('execution_id', '—')}`",
        f"- mutation_performed: **{str(getattr(result, 'mutation_performed', False)).lower()}**",
        f"- idempotent_replay: **{str(getattr(result, 'idempotent_replay', False)).lower()}**",
        f"- policy_blocked: **{str(getattr(result, 'policy_blocked', False)).lower()}**",
        f"- deployment_id: `{metadata.get('deployment_id') or journal.get('railway_deployment_id') or '—'}`",
        f"- graphql_operation: `{metadata.get('graphql_operation', '—')}`",
    ]
    if getattr(result, "detail", ""):
        lines.extend(["", str(result.detail)])
    errors = list(getattr(result, "errors", None) or [])
    if errors:
        lines.extend(["", "Errors:"])
        for err in errors:
            lines.append(f"- {err}")
    lines.extend(
        [
            "",
            "FIX 113 stops after deploy trigger. Runtime verification is FIX 114.",
        ]
    )
    return "\n".join(lines)


def render_readonly_runtime_verification_result(result: Any) -> str:
    journal = result.journal if hasattr(result, "journal") else {}
    verification = (
        journal.get("runtime_verification") if isinstance(journal.get("runtime_verification"), dict) else {}
    )
    lines = [
        "# Railway Runtime Verification (Read-only, FIX 114)",
        "",
        f"- execution_id: `{journal.get('execution_id', '—')}`",
        f"- mutation_performed: **{str(getattr(result, 'mutation_performed', False)).lower()}**",
        f"- idempotent_replay: **{str(getattr(result, 'idempotent_replay', False)).lower()}**",
        f"- policy_blocked: **{str(getattr(result, 'policy_blocked', False)).lower()}**",
        f"- runtime_verification_performed: **{str(journal.get('runtime_verification_performed', False)).lower()}**",
        f"- deployment_id: `{verification.get('deployment_id') or journal.get('railway_deployment_id') or '—'}`",
        f"- deployment_state: `{verification.get('deployment_state', '—')}`",
        f"- verified: **{str(verification.get('verified', False)).lower()}**",
    ]
    if getattr(result, "detail", ""):
        lines.extend(["", str(result.detail)])
    errors = list(getattr(result, "errors", None) or [])
    if errors:
        lines.extend(["", "Errors:"])
        for err in errors:
            lines.append(f"- {err}")
    lines.extend(
        [
            "",
            "Read-only check only; deploy was not re-triggered.",
        ]
    )
    return "\n".join(lines)


def render_runtime_verification_readiness(readiness: Any) -> str:
    lines = [
        "# Railway Runtime Verification Readiness (FIX 114 Gate)",
        "",
        f"- ready_for_runtime_verification: **{str(getattr(readiness, 'ready_for_runtime_verification', False)).lower()}**",
        f"- verify_runtime_enabled: **{str(getattr(readiness, 'verify_runtime_enabled', False)).lower()}**",
        f"- trigger_deploy_live_success: **{str(getattr(readiness, 'trigger_deploy_live_success', False)).lower()}**",
        f"- deployment_id_present: **{str(getattr(readiness, 'deployment_id_present', False)).lower()}**",
        f"- env_names_verified: **{str(getattr(readiness, 'env_names_verified', False)).lower()}**",
        f"- deploy_prerequisites_met: **{str(getattr(readiness, 'deploy_prerequisites_met', False)).lower()}**",
        f"- final_phrase_present: **{str(getattr(readiness, 'final_phrase_present', False)).lower()}**",
    ]
    messages = list(getattr(readiness, "messages", None) or [])
    if messages:
        lines.extend(["", "Notes:"])
        for msg in messages:
            lines.append(f"- {msg}")
    blockers = list(getattr(readiness, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    return "\n".join(lines)


def render_runtime_verification_status(*, journal: dict[str, Any]) -> str:
    verification = (
        journal.get("runtime_verification") if isinstance(journal.get("runtime_verification"), dict) else {}
    )
    lines = [
        "# Railway Runtime Verification Status",
        "",
        f"- execution_id: `{journal.get('execution_id', '—')}`",
        f"- runtime_verification_performed: **{str(journal.get('runtime_verification_performed', False)).lower()}**",
        f"- railway_deployment_id: `{journal.get('railway_deployment_id', '—')}`",
        f"- verified: **{str(verification.get('verified', False)).lower()}**",
        f"- deployment_state: `{verification.get('deployment_state', '—')}`",
        f"- readonly: **{str(verification.get('readonly', True)).lower()}**",
    ]
    detail = str(verification.get("detail") or "")
    if detail:
        lines.extend(["", detail])
    if not journal.get("runtime_verification_performed"):
        lines.extend(
            [
                "",
                "Runtime verification has not run yet. Use `show railway runtime verification readiness` "
                "then `execute railway runtime verification` when gates pass.",
            ]
        )
    return "\n".join(lines)


def render_deploy_trigger_readiness(readiness: Any) -> str:
    lines = [
        "# Railway Deploy Trigger Readiness (FIX 113 Gate)",
        "",
        f"- ready_for_deploy_trigger: **{str(getattr(readiness, 'ready_for_deploy_trigger', False)).lower()}**",
        f"- deploy_trigger_enabled: **{str(getattr(readiness, 'deploy_trigger_enabled', False)).lower()}**",
        f"- create_service_live_success: **{str(getattr(readiness, 'create_service_live_success', False)).lower()}**",
        f"- connect_source_live_success: **{str(getattr(readiness, 'connect_source_live_success', False)).lower()}**",
        f"- configure_env_live_success: **{str(getattr(readiness, 'configure_env_live_success', False)).lower()}**",
        f"- env_names_verified: **{str(getattr(readiness, 'env_names_verified', False)).lower()}**",
        f"- staging_only: **{str(getattr(readiness, 'staging_only', False)).lower()}**",
        f"- final_phrase_present: **{str(getattr(readiness, 'final_phrase_present', False)).lower()}**",
        f"- rollback_contract_visible: **{str(getattr(readiness, 'rollback_contract_visible', False)).lower()}**",
    ]
    messages = list(getattr(readiness, "messages", None) or [])
    if messages:
        lines.extend(["", "Notes:"])
        for msg in messages:
            lines.append(f"- {msg}")
    blockers = list(getattr(readiness, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    return "\n".join(lines)


def render_env_configure_audit(audit: Any) -> str:
    lines = [
        "# Railway Env Configure Audit",
        "",
        f"- audit_ok: **{str(getattr(audit, 'ok', False)).lower()}**",
        f"- skip_deploys_enforced: **{str(getattr(audit, 'skip_deploys_enforced_in_code', False)).lower()}**",
        f"- env_only_stage_validation: **{str(getattr(audit, 'env_only_stage_validation', False)).lower()}**",
        f"- blocks_chat_secrets: **{str(getattr(audit, 'blocks_chat_secrets_in_executor', False)).lower()}**",
        f"- blocks_local_env: **{str(getattr(audit, 'blocks_local_env_resolution', False)).lower()}**",
        f"- no_deploy_trigger_in_adapter: **{str(getattr(audit, 'no_deploy_trigger_in_adapter', False)).lower()}**",
        f"- rollback_contract_visible: **{str(getattr(audit, 'rollback_contract_visible', False)).lower()}**",
        f"- rollback_plan_ready: **{str(getattr(audit, 'rollback_plan_ready', False)).lower()}**",
    ]
    proofs = list(getattr(audit, "idempotent_proofs", None) or [])
    if proofs:
        lines.extend(["", "Idempotent replay proofs:"])
        for proof in proofs:
            lines.append(
                f"- `{getattr(proof, 'group_id', '—')}`: would_skip=**{str(getattr(proof, 'would_skip_on_replay', False)).lower()}** "
                f"(journal={str(getattr(proof, 'journal_recorded', False)).lower()}, "
                f"receipt={str(getattr(proof, 'receipt_recorded', False)).lower()}, "
                f"fingerprint=`{getattr(proof, 'version_fingerprint', '')}`)"
            )
    verification = getattr(audit, "verification", None)
    if verification is not None:
        lines.extend(
            [
                "",
                "Read-only verification:",
                f"- verified: **{str(getattr(verification, 'verified', False)).lower()}**",
                f"- names_observed: `{', '.join(getattr(verification, 'names_observed', ()) or ()) or '—'}`",
            ]
        )
    blockers = list(getattr(audit, "blockers", None) or [])
    if blockers:
        lines.extend(["", "Blockers:"])
        for code in blockers:
            lines.append(f"- {code}")
    return "\n".join(lines)


def render_approval_blockers(blockers: list[str]) -> str:
    """Legacy terse blocker list — prefer render_execution_request_blockers."""
    missing = ", ".join(blockers) if blockers else "approval prerequisites"
    return "\n".join(
        [
            "Cannot request Railway service creation execution yet.",
            "",
            f"Blocked until: {missing}",
            "",
            "Complete simulation and approvals first, then retry when execution is enabled.",
            "",
            "No Railway mutation has been performed.",
        ]
    )
