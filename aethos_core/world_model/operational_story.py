# SPDX-License-Identifier: Apache-2.0
"""Operational story generation from investigation state."""

from __future__ import annotations

from aethos_core.world_model.hypothesis_graph import leading_hypothesis
from aethos_core.world_model.investigation_state import InvestigationState


def _service_name(state: InvestigationState) -> str:
    return state.service or state.target.split("/")[-1].strip() or "the service"


def compose_investigation_recap(state: InvestigationState) -> str:
    service = _service_name(state)
    project = state.project.strip()
    if project:
        opener = f"We're investigating the failed **{service}** service in **{project}**."
    else:
        opener = f"We're still investigating the **{service}** failure."
    lines = [opener, "", "Current understanding:"]
    if "failed_runtime_status" in state.evidence:
        lines.append(f"- **{service}** is unhealthy.")
    if "fresh_wiredtiger_logs" in state.evidence:
        lines.append("- Runtime logs are fresh but low-signal.")
        lines.append("- Logs mostly show WiredTiger storage-engine activity.")
    elif "fresh_runtime_logs" in state.evidence or "runtime_logs" in state.evidence:
        lines.append("- Runtime logs are fresh but low-signal.")
    if "stale_service_events" in state.evidence:
        lines.append("- Service events are stale and do not explain the current failure.")
    elif "fresh_service_events" in state.evidence:
        lines.append("- Recent service events are available and aligned with the investigation.")
    if "high_signal_logs" not in state.evidence:
        lines.append("- No fatal database/runtime error has been observed yet.")

    leading = leading_hypothesis(state)
    if leading:
        lines.extend(["", "Current hypothesis:", f"- {leading.label} — {state.confidence_label} confidence"])

    if state.missing_evidence:
        lines.extend(["", "Missing evidence:"])
        for item in state.missing_evidence[:5]:
            lines.append(f"- {item}")

    action, _key = state.next_best_action, state.next_best_action_key
    if not action:
        from aethos_core.world_model.investigation_planner import plan_next_action_from_state

        action, _key = plan_next_action_from_state(state)
    lines.extend(["", "Best next step:", action, "", "No mutation is recommended yet."])
    return "\n".join(lines)


def compose_next_step_answer(state: InvestigationState) -> str:
    service = _service_name(state)
    from aethos_core.repair_memory.recommendation_guard import compose_next_step_with_repair_guard
    from aethos_core.world_model.investigation_planner import plan_next_action_from_state

    action, _key = state.next_best_action, state.next_best_action_key
    if not action:
        action, _key = plan_next_action_from_state(state)
    lines = ["Best next step:", action]
    reasons: list[str] = []
    if "fresh_wiredtiger_logs" in state.evidence or "fresh_runtime_logs" in state.evidence:
        reasons.append("current logs are fresh but low-signal")
    if "stale_service_events" in state.evidence:
        reasons.append("service events are stale")
    if "high_signal_logs" not in state.evidence:
        reasons.append("no fatal error or exit reason has been confirmed yet")
    if reasons:
        lines.extend(["", "Reason:", f"{' and '.join(reasons).capitalize()} for **{service}**."])
    return compose_next_step_with_repair_guard(state, "\n".join(lines))


def compose_continuation_intro(state: InvestigationState, *, action: str) -> str:
    service = _service_name(state)
    if action == "logs":
        return f"Continuing the **{service}** investigation — here are the latest logs I collected:"
    if action == "events":
        return f"Continuing the **{service}** investigation — here are the latest service events:"
    if action == "diagnosis":
        return f"We're still investigating the **{service}** failure."
    return f"Continuing the active investigation for **{service}**."


def compose_restart_safety_answer(state: InvestigationState) -> str:
    service = _service_name(state)
    from aethos_core.repair_memory.recommendation_guard import compose_restart_again_reply
    from aethos_core.world_model.investigation_planner import plan_next_action_from_state

    blocked = compose_restart_again_reply(state)
    if blocked:
        return blocked

    if state.confidence_score < 0.6:
        action, _key = state.next_best_action, state.next_best_action_key
        if not action:
            action, _key = plan_next_action_from_state(state)
        lines = [
            "Not yet.",
            "",
            "Restart is not recommended right now because the investigation confidence is still "
            f"**{state.confidence_label}** and the root cause is unconfirmed.",
            "",
            "Current evidence:",
        ]
        if "failed_runtime_status" in state.evidence:
            lines.append(f"- **{service}** is failed.")
        if "fresh_wiredtiger_logs" in state.evidence:
            lines.append("- Logs only show WiredTiger startup/storage activity.")
        elif "fresh_runtime_logs" in state.evidence or "runtime_logs" in state.evidence:
            lines.append("- Runtime logs are available but low-signal.")
        if "high_signal_logs" not in state.evidence:
            lines.append("- No fatal error or exit reason has been confirmed.")
        if "stale_service_events" in state.evidence:
            lines.append("- Service events are stale.")
        lines.extend(["", "Safer next step:", action, "", "No mutation has been performed."])
        return "\n".join(lines)

    leading = leading_hypothesis(state)
    label = leading.label if leading else "the current failure"
    return (
        f"Restart may be considered for **{service}**, but only with explicit approval.\n\n"
        f"Current leading hypothesis: **{label}** ({state.confidence_label} confidence).\n"
        f"Best next step before restart: {state.next_best_action or 'verify surrounding logs and service events.'}"
    )


def compose_hypothesis_summary(state: InvestigationState) -> str:
    service = _service_name(state)
    leading = leading_hypothesis(state)
    if leading is None:
        return f"No leading hypothesis is established yet for **{service}**."
    return (
        f"Current hypothesis for **{service}**:\n\n"
        f"- **{leading.label}** ({state.confidence_label} confidence, score {state.confidence_score:.2f})"
    )


def compose_missing_evidence_summary(state: InvestigationState) -> str:
    service = _service_name(state)
    if not state.missing_evidence:
        return f"No major evidence gaps are recorded for **{service}** right now."
    lines = [f"Missing evidence for **{service}**:", ""]
    for item in state.missing_evidence[:6]:
        lines.append(f"- {item}")
    return "\n".join(lines)


def compose_blocker_summary(state: InvestigationState) -> str:
    service = _service_name(state)
    from aethos_core.world_model.investigation_planner import plan_next_action_from_state

    action, _key = state.next_best_action, state.next_best_action_key
    if not action:
        action, _key = plan_next_action_from_state(state)
    blockers: list[str] = []
    if state.confidence_score < 0.6:
        blockers.append(f"investigation confidence is still **{state.confidence_label}**")
    if state.missing_evidence:
        blockers.append("key evidence is still missing")
    if "stale_service_events" in state.evidence:
        blockers.append("service events are stale")
    if not blockers:
        blockers.append("root cause has not been fully confirmed")
    lines = [f"What is blocking progress on **{service}**:", ""]
    for item in blockers:
        lines.append(f"- {item.capitalize()}")
    lines.extend(["", "Best next step:", action])
    return "\n".join(lines)


def compose_investigation_status(state: InvestigationState) -> str:
    service = _service_name(state)
    lines = [
        f"Investigation status for **{service}**:",
        "",
        f"- Confidence: **{state.confidence_label}** ({state.confidence_score:.2f})",
        f"- Evidence tags collected: **{len(state.evidence)}**",
        f"- Completed checks: **{', '.join(state.completed_checks) or 'none'}**",
    ]
    if state.conclusion:
        lines.extend(["", state.conclusion])
    return "\n".join(lines)


def compose_what_changed_recap(state: InvestigationState, *, previous_evidence: list[str]) -> str:
    service = _service_name(state)
    added = sorted(set(state.evidence) - set(previous_evidence))
    lines = [f"Investigation update for **{service}**:", ""]
    if added:
        lines.append("New evidence since the last turn:")
        for item in added:
            lines.append(f"- {item.replace('_', ' ')}")
    else:
        lines.append("No materially new evidence tags were added on this turn.")
    if state.conclusion:
        lines.extend(["", state.conclusion])
    return "\n".join(lines)
