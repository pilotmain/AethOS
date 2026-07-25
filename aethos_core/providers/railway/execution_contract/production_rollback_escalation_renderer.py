# SPDX-License-Identifier: Apache-2.0
"""FIX 120 — production rollback escalation renderers."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.production_rollback_escalation import (
    RollbackEscalationGateResult,
    load_rollback_escalation_config,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_contract import (
    INCIDENT_COMMANDER_ACK_PHRASE,
    PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_store import (
    rollback_rehearsal_quorum_count,
)


def render_rollback_escalation_ticket(record: dict[str, Any]) -> str:
    lines = [
        "# Railway Production Rollback Escalation",
        "",
        f"- escalation_id: `{record.get('escalation_id', '—')}`",
        f"- execution_id: `{record.get('execution_id', '—')}`",
        f"- decision_state: **{record.get('decision_state', '—')}**",
        f"- rollback_recommendation: **{record.get('rollback_recommendation', '—')}**",
        f"- incident_escalation: **{record.get('incident_escalation', '—')}**",
        f"- verification_passed: **{str(record.get('verification_passed')).lower()}**",
        f"- autonomous_rollback_permitted: **false**",
        f"- verification_receipt_id: `{record.get('verification_receipt_id') or '—'}`",
        "",
        "Evidence bundle is attached on this ticket (no secret values).",
        "",
        "## Rollback rehearsal confirmations",
    ]
    confirmations = record.get("rollback_rehearsal_confirmations") or []
    if not confirmations:
        lines.append("- none recorded")
    else:
        for row in confirmations:
            lines.append(f"- {row.get('kind')} @ {row.get('recorded_at')}")
    cfg = load_rollback_escalation_config()
    lines.extend(
        [
            "",
            f"Quorum progress: **{rollback_rehearsal_quorum_count(record)}** / {cfg['rehearsal_quorum_required']}",
            "",
            "Required phrases:",
            f"- Incident commander: `{INCIDENT_COMMANDER_ACK_PHRASE}`",
            f"- Rollback rehearsal quorum: `{PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE}`",
            "",
            "No live production rollback will be executed.",
        ]
    )
    return "\n".join(lines)


def render_rollback_escalation_audit_trail(record: dict[str, Any]) -> str:
    lines = [
        "# Railway Production Rollback Audit Trail",
        "",
        f"- escalation_id: `{record.get('escalation_id', '—')}`",
        f"- execution_id: `{record.get('execution_id', '—')}`",
        f"- current_state: **{record.get('decision_state', '—')}**",
        "",
        "Events:",
    ]
    trail = record.get("audit_trail") or []
    if not trail:
        lines.append("- none")
    else:
        for event in trail:
            lines.append(
                f"- [{event.get('recorded_at')}] **{event.get('action')}** "
                f"({event.get('actor')}) state={event.get('state')} — {event.get('detail', '')}"
            )
    lines.extend(["", "Human decisions are audited; autonomous rollback is prohibited."])
    return "\n".join(lines)


def render_rollback_escalation_gate(gate: RollbackEscalationGateResult) -> str:
    lines = [
        "# Railway Production Rollback Rehearsal Quorum",
        "",
        f"- ready_for_shadow_rehearsal: **{str(gate.ready_for_shadow_rehearsal).lower()}**",
        f"- escalation_present: **{str(gate.escalation_present).lower()}**",
        f"- decision_state: **{gate.decision_state or '—'}**",
        f"- incident_commander_acknowledged: **{str(gate.incident_commander_acknowledged).lower()}**",
        f"- rollback_rehearsal_quorum_satisfied: **{str(gate.rollback_rehearsal_quorum_satisfied).lower()}**",
    ]
    if gate.blockers:
        lines.extend(["", "Blockers:"])
        for code in gate.blockers:
            lines.append(f"- `{code}`")
    if gate.messages:
        lines.extend(["", "Messages:"])
        for msg in gate.messages:
            lines.append(f"- {msg}")
    lines.append("\nNo Railway mutation has been performed.")
    return "\n".join(lines)
