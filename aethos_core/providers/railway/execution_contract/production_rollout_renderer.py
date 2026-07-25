# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — production rollout orchestration renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.production_rollout_gate import (
    RolloutStageGateResult,
    assess_rollout_health_checkpoints,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration import (
    RolloutOrchestrationResult,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED,
    ROLLOUT_ADVANCE_APPROVAL_PHRASE,
    ROLLOUT_PAUSE_PHRASE,
    ROLLOUT_RESUME_PHRASE,
    ROLLOUT_STAGES,
)
from aethos_core.providers.railway.execution_contract.production_rollout_receipts import (
    list_rollout_receipts,
)


def render_rollout_status(status: dict[str, Any]) -> str:
    journal = status.get("journal") or {}
    gate = status.get("gate") or {}
    lines = [
        "# Railway Production Rollout Orchestration",
        "",
        f"- execution_id: `{journal.get('execution_id', '')}`",
        f"- orchestration_state: **{journal.get('orchestration_state', '')}**",
        f"- current_stage: **{status.get('current_stage', '')}**",
        f"- blast_radius: **{journal.get('blast_radius', '')}**",
        f"- rollout_paused: **{journal.get('rollout_paused', False)}**",
        f"- completed_stages: {', '.join(status.get('completed_stages') or []) or '—'}",
        f"- verification_passed: **{status.get('verification_passed', False)}**",
        f"- autonomous_promotion_permitted: **{AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED}**",
        f"- live_mutation_boundary: **{journal.get('live_mutation_boundary', 'blocked')}**",
        f"- ready_to_advance_current: **{gate.get('ready_to_advance', False)}**",
        "",
        "## Rollout stages",
    ]
    stage_status = journal.get("stage_status") or {}
    for stage in ROLLOUT_STAGES:
        lines.append(f"- `{stage}`: {stage_status.get(stage, 'pending')}")
    blockers = gate.get("blockers") or []
    if blockers:
        lines.extend(["", "## Blockers"])
        for b in blockers:
            lines.append(f"- `{b}`")
    lines.extend(
        [
            "",
            "## Human approval phrases",
            f"- Advance: {ROLLOUT_ADVANCE_APPROVAL_PHRASE}",
            f"- Pause: {ROLLOUT_PAUSE_PHRASE}",
            f"- Resume: {ROLLOUT_RESUME_PHRASE}",
        ]
    )
    return "\n".join(lines)


def render_rollout_timeline(*, execution_id: str, journal: dict[str, Any]) -> str:
    receipts = list_rollout_receipts(execution_id=execution_id)
    lines = [
        "# Railway Production Rollout Timeline",
        "",
        f"execution_id: `{execution_id}`",
        f"rollout_id: `{journal.get('rollout_id', '')}`",
        "",
    ]
    if not receipts:
        lines.append("_No rollout receipts yet._")
        return "\n".join(lines)
    for row in receipts:
        lines.extend(
            [
                f"## {row.get('stage', '')} — {row.get('action', '')}",
                f"- status: {row.get('status', '')}",
                f"- mutation_performed: **{row.get('mutation_performed', False)}**",
                f"- recorded_at: {row.get('recorded_at', '')}",
                f"- detail: {row.get('detail', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def render_rollout_health_checkpoints(
    *,
    execution_id: str,
    stage: str,
    plan: dict[str, Any] | None,
) -> str:
    checkpoints = assess_rollout_health_checkpoints(
        execution_id=execution_id,
        stage=stage,  # type: ignore[arg-type]
        plan=plan,
    )
    lines = [
        "# Railway Production Rollout Health Checkpoints",
        "",
        f"- stage: **{stage}**",
        "",
    ]
    for cp in checkpoints:
        mark = "pass" if cp.passed else "FAIL"
        lines.append(f"- `{cp.checkpoint_id}`: **{mark}** — {cp.detail}")
    return "\n".join(lines)


def render_rollout_gate(gate: RolloutStageGateResult) -> str:
    lines = [
        "# Railway Production Rollout Gate",
        "",
        f"- stage: **{gate.stage}**",
        f"- ready_to_advance: **{gate.ready_to_advance}**",
        f"- rollout_paused: **{gate.rollout_paused}**",
        f"- blast_radius: **{gate.blast_radius}**",
        "",
        "## Health checkpoints",
    ]
    for cp in gate.health_checkpoints:
        mark = "pass" if cp.passed else "FAIL"
        lines.append(f"- `{cp.checkpoint_id}`: **{mark}**")
    if gate.blockers:
        lines.extend(["", "## Blockers"])
        for b in gate.blockers:
            lines.append(f"- `{b}`")
    if gate.messages:
        lines.extend(["", "## Messages"])
        for m in gate.messages:
            lines.append(f"- {m}")
    return "\n".join(lines)


def render_rollout_orchestration_result(result: RolloutOrchestrationResult) -> str:
    lines = [
        "# Railway Production Rollout Action",
        "",
        f"- success: **{result.success}**",
        f"- action: **{result.action}**",
        f"- orchestration_state: **{result.journal.get('orchestration_state', '')}**",
        f"- current_stage: **{result.journal.get('current_stage', '')}**",
    ]
    if result.stage_advanced_to:
        lines.append(f"- stage_advanced_to: **{result.stage_advanced_to}**")
    lines.append(f"- detail: {result.detail}")
    if result.blockers:
        lines.extend(["", "## Blockers"])
        for b in result.blockers:
            lines.append(f"- `{b}`")
    return "\n".join(lines)
