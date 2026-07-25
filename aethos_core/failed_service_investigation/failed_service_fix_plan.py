# SPDX-License-Identifier: Apache-2.0
"""Governed fix plans for failed services from health report context."""

from __future__ import annotations

from typing import Any

from aethos_core.failed_service_investigation.failed_service_diagnosis import collect_failed_service_evidence
from aethos_core.failed_service_investigation.failed_service_resolver import ResolvedFailedService


def compose_fix_plan_reply(
    target: ResolvedFailedService,
    *,
    session_id: str = "default",
) -> tuple[str, dict[str, Any]]:
    evidence = collect_failed_service_evidence(target)
    from aethos_core.world_model.confidence_tracker import mutation_allowed
    from aethos_core.world_model.investigation_engine import update_investigation_from_evidence

    state = update_investigation_from_evidence(
        session_id=session_id,
        evidence=evidence,
        investigation_kind="fix_plan",
        operator_intent="create_fix_plan",
    )
    row = evidence["target"]
    label = evidence["target_label"]
    root = dict(evidence.get("root_cause") or {})
    correlation = dict(evidence.get("evidence_correlation") or {})

    logs_state = "available" if evidence.get("logs_available") else "unavailable"
    lines = [
        f"Fix plan for **{label}**",
        "",
        "Known state:",
        f"- Railway status: **{evidence.get('status', 'unknown')}** / health **{evidence.get('health', 'unknown')}**",
        f"- Latest deployment: **{evidence.get('deployment_state', 'unknown')}**",
        f"- Logs: **{logs_state}**",
        f"- Failure class: **{root.get('label', 'Unknown')}** (confidence: {root.get('confidence', 'low')})",
        f"- Investigation confidence: **{state.confidence_label}** ({state.confidence_score:.2f})",
        "",
        "Evidence to check:",
    ]

    next_checks = list(root.get("next_checks") or [])
    if next_checks:
        for idx, check in enumerate(next_checks[:5], start=1):
            lines.append(f"{idx}. {check}")
    else:
        lines.append("1. Refresh Railway deployment/runtime logs")
        lines.append("2. Inspect service events and exit code")
        lines.append("3. Verify env/config and dependency connectivity")

    signals = list(root.get("log_signals") or [])
    if signals:
        lines.extend(["", "Latest crash / failure signals:"])
        for signal in signals[:3]:
            lines.append(f"- `{signal}`")

    interpretation = list(root.get("interpretation") or [])
    if interpretation:
        lines.extend(["", "Interpretation:"])
        for item in interpretation[:3]:
            lines.append(f"- {item}")

    lines.extend(["", "Plan:"])
    lines.append("1. Collect the evidence above before any mutation")
    lines.append("2. Confirm root cause category with surrounding logs/events")
    allow_mutation = mutation_allowed(state.confidence_score, root=root)
    if allow_mutation and root.get("suggested_operation"):
        lines.append(
            f"3. Only then consider **{str(root.get('suggested_operation')).title()}** with explicit approval"
        )
    else:
        lines.append("3. Do **not** restart/redeploy yet — current investigation confidence is not strong enough")
    lines.append("4. Verify runtime logs and health after any approved mutation")

    if correlation.get("best_next_step"):
        lines.extend(["", "Best next action:", correlation["best_next_step"]])

    gaps = list(root.get("evidence_gaps") or [])
    if gaps or not evidence.get("logs_available"):
        lines.extend(["", "Evidence gaps:"])
        if not evidence.get("logs_available"):
            lines.append("- Deployment/runtime logs were not available during plan generation")
        for gap in gaps:
            lines.append(f"- {gap}")

    recommended = list(root.get("recommended_actions") or [])
    if recommended:
        lines.extend(["", "Recommended next commands:"])
        for action in recommended[:3]:
            lines.append(f'- "{action}"')

    plan = {
        "ok": allow_mutation,
        "summary": str(root.get("summary") or "Evidence-based fix plan"),
        "proposed_operation": root.get("suggested_operation") if allow_mutation else None,
        "proposed_changes": list(root.get("next_checks") or []),
        "requires_approval": True,
        "preflight_required": True,
        "root_cause": root,
        "confidence_score": state.confidence_score,
        "confidence_label": state.confidence_label,
    }

    lines.extend(["", "No mutation has been performed yet."])
    return "\n".join(lines), plan
