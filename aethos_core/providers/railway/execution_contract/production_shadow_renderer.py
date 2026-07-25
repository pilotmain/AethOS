# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — production shadow rehearsal renderers."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.production_confirmation_store import (
    list_confirmations,
    quorum_counts,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    assess_railway_production_policy,
    is_deployment_freeze_active,
    load_railway_production_policy_config,
)
from aethos_core.providers.railway.execution_contract.production_shadow_certification import (
    ProductionShadowCertificationReport,
)
from aethos_core.providers.railway.execution_contract.production_shadow_contract_models import (
    FORWARD_SHADOW_PHASES,
    ROLLBACK_SHADOW_PHASES,
)
from aethos_core.providers.railway.execution_contract.production_shadow_gate import (
    ProductionShadowGateResult,
)
from aethos_core.providers.railway.execution_contract.production_shadow_executor import (
    ProductionShadowOrchestrationResult,
)
from aethos_core.providers.railway.execution_contract.production_shadow_receipts import (
    list_shadow_receipts,
)


def render_production_shadow_status(
    *,
    gate: ProductionShadowGateResult,
    execution_id: str,
) -> str:
    journal_state = "—"
    if execution_id:
        from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
            load_shadow_journal,
        )

        j = load_shadow_journal(execution_id=execution_id)
        if j:
            journal_state = str(j.get("state") or "—")
    lines = [
        "# Railway Production Shadow Status",
        "",
        f"- shadow_execution_enabled: **{str(gate.shadow_execution_enabled).lower()}**",
        f"- production_target: **{str(gate.production_target).lower()}**",
        f"- gate_ready: **{str(gate.ready).lower()}**",
        f"- operator_quorum_satisfied: **{str(gate.operator_quorum_satisfied).lower()}**",
        f"- forward_live_permitted: **{str(gate.forward_live_permitted).lower()}**",
        f"- shadow_journal_state: {journal_state}",
        "",
        "Expected shadow forward timeline:",
    ]
    for phase in FORWARD_SHADOW_PHASES:
        lines.append(f"- {phase}")
    lines.extend(["", "Expected shadow rollback timeline:"])
    for phase in ROLLBACK_SHADOW_PHASES:
        lines.append(f"- {phase}")
    lines.append("- rollback_shadow")
    if gate.blockers:
        lines.extend(["", "Blockers:"])
        for code in gate.blockers:
            lines.append(f"- `{code}`")
    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)


def render_production_shadow_timeline(*, execution_id: str) -> str:
    receipts = list_shadow_receipts(execution_id=execution_id)
    lines = [
        "# Railway Production Shadow Timeline",
        "",
        f"execution_id: `{execution_id}`",
        "",
    ]
    if not receipts:
        lines.append("No shadow receipts recorded yet.")
    else:
        for row in receipts:
            lines.extend(
                [
                    f"## {row.get('phase')}",
                    f"- status: {row.get('status')}",
                    f"- mutation_performed: **{str(row.get('mutation_performed')).lower()}**",
                    f"- execution_mode: {row.get('execution_mode')}",
                    "",
                ]
            )
    lines.append("No Railway mutation has been performed.")
    return "\n".join(lines)


def render_production_shadow_orchestration_result(result: ProductionShadowOrchestrationResult) -> str:
    lines = [
        "# Railway Production Shadow Rehearsal",
        "",
        f"- policy_blocked: **{str(result.policy_blocked).lower()}**",
        f"- shadow_completed: **{str(result.shadow_completed).lower()}**",
        f"- executed_phases: {', '.join(result.executed_phases) or '—'}",
        f"- skipped_phases: {', '.join(result.skipped_phases) or '—'}",
        "",
        result.detail,
    ]
    if result.blockers:
        lines.extend(["", "Blockers:"])
        for code in result.blockers:
            lines.append(f"- `{code}`")
    execution_id = str(result.journal.get("execution_id") or "")
    if execution_id:
        lines.extend(["", render_production_shadow_timeline(execution_id=execution_id)])
    return "\n".join(lines)


def render_production_shadow_certification(report: ProductionShadowCertificationReport) -> str:
    lines = [
        "# Railway Production Shadow Certification",
        "",
        f"- certification_ok: **{str(report.ok).lower()}**",
        f"- shadow_execution_enabled: **{str(report.shadow_execution_enabled).lower()}**",
        "",
        "Checks:",
    ]
    for row in report.checks:
        status = "pass" if row.get("pass") else "fail"
        lines.append(f"- {row.get('name')}: **{status}**")
    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)


def render_production_quorum_status(*, execution_id: str) -> str:
    counts = quorum_counts(execution_id=execution_id) if execution_id else {}
    rows = list_confirmations(execution_id=execution_id) if execution_id else []
    cfg = load_railway_production_policy_config()
    lines = [
        "# Railway Production Quorum Status",
        "",
        f"- quorum_required: **{cfg.operator_quorum_required}**",
        f"- second_confirmation_required: **{str(cfg.require_second_confirmation).lower()}**",
        f"- distinct_confirmations: **{int(counts.get('total_distinct') or 0)}**",
        "",
        "Recorded confirmations:",
    ]
    if not rows:
        lines.append("- none")
    else:
        for row in rows:
            lines.append(f"- {row.get('kind')} @ {row.get('recorded_at')}")
    lines.extend(["", "No Railway mutation has been performed."])
    return "\n".join(lines)


def render_production_freeze_status() -> str:
    cfg = load_railway_production_policy_config()
    active = is_deployment_freeze_active()
    lines = [
        "# Railway Production Freeze Status",
        "",
        f"- deployment_freeze_flag: **{str(cfg.deployment_freeze).lower()}**",
        f"- freeze_window_active: **{str(active).lower()}**",
        f"- freeze_start_utc: {cfg.freeze_start_utc or '—'}",
        f"- freeze_end_utc: {cfg.freeze_end_utc or '—'}",
        "",
        "No Railway mutation has been performed.",
    ]
    return "\n".join(lines)


def render_production_incident_mode_status() -> str:
    cfg = load_railway_production_policy_config()
    lines = [
        "# Railway Production Incident Mode",
        "",
        f"- incident_mode_active: **{str(cfg.incident_mode).lower()}**",
        "",
        "When true, production shadow rehearsal and live execution are frozen.",
        "",
        "No Railway mutation has been performed.",
    ]
    return "\n".join(lines)
