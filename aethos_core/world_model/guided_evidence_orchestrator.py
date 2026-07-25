# SPDX-License-Identifier: Apache-2.0
"""Guided read-only evidence collection for strategic investigation follow-ups."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.failed_service_investigation.failed_service_memory import get_health_report_rows, row_key
from aethos_core.failed_service_investigation.failed_service_resolver import ResolvedFailedService
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome
from aethos_core.world_model.investigation_state import InvestigationState

_GUIDED_ACTION_KEYS = frozenset(
    {
        "refresh_events_and_fetch_failure_window_logs",
        "fetch_failure_window_logs",
        "deeper_evidence_inspection",
        "investigate",
    }
)

_GATHERING_BULLETS = (
    "fetching surrounding failure logs",
    "inspecting Railway service events",
    "correlating deployment timestamps",
)


@dataclass
class GuidedEvidenceResult:
    ok: bool
    evidence: dict[str, Any] | None = None
    investigation_state: InvestigationState | None = None
    error: str = ""
    meta: dict[str, str] = field(default_factory=dict)


def should_execute_guided_evidence(
    *,
    state: InvestigationState | None,
    outcome: RepairAttemptOutcome | None,
) -> bool:
    if outcome is not None and outcome.helped:
        return False
    if outcome is not None and not outcome.helped:
        return True
    if state is None:
        return False
    if state.confidence_score < 0.75:
        return True
    if state.next_best_action_key in _GUIDED_ACTION_KEYS:
        return True
    if any(
        tag in state.evidence
        for tag in ("stale_service_events", "failed_restart_attempt", "restart_did_not_resolve")
    ):
        return True
    return False


def can_execute_readonly_guided_evidence() -> tuple[bool, str]:
    try:
        from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

        token, _, err = resolve_railway_mutation_credentials()
        if token:
            return True, ""
        return False, err or "Railway read credentials are not configured."
    except Exception as exc:
        return False, str(exc)


def resolve_target_row_for_guided_collection(
    *,
    state: InvestigationState | None,
    outcome: RepairAttemptOutcome | None,
    session_id: str,
) -> dict[str, Any] | None:
    base: dict[str, Any] | None = None
    if state is not None and state.service:
        base = {
            "service": state.service,
            "project": state.project,
            "environment": state.environment,
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
        }
    elif outcome is not None and outcome.service:
        base = {
            "service": outcome.service,
            "project": outcome.project,
            "environment": outcome.environment,
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
        }

    if base is None:
        return None

    for health_row in get_health_report_rows(session_id=session_id):
        same_key = row_key(health_row) == row_key(base)
        same_service = str(health_row.get("service") or "").lower() == str(base.get("service") or "").lower()
        if same_key or same_service:
            merged = dict(base)
            merged.update({key: value for key, value in health_row.items() if value not in (None, "")})
            return merged
    return base


def execute_guided_evidence_collection(
    *,
    session_id: str,
    state: InvestigationState | None,
    outcome: RepairAttemptOutcome | None,
) -> GuidedEvidenceResult:
    row = resolve_target_row_for_guided_collection(state=state, outcome=outcome, session_id=session_id)
    if row is None:
        return GuidedEvidenceResult(ok=False, error="No investigation target available for guided evidence collection.")

    can_run, cred_error = can_execute_readonly_guided_evidence()
    if not can_run:
        return GuidedEvidenceResult(ok=False, error=cred_error)

    from aethos_core.failed_service_investigation.failed_service_diagnosis import collect_failed_service_evidence
    from aethos_core.world_model.investigation_engine import update_investigation_from_evidence

    try:
        evidence = collect_failed_service_evidence(ResolvedFailedService(row=row))
    except Exception as exc:
        return GuidedEvidenceResult(ok=False, error=str(exc))

    updated_state = update_investigation_from_evidence(
        session_id=session_id,
        evidence=evidence,
        investigation_kind="guided_evidence_collection",
        operator_intent="guided_evidence_collection",
    )
    meta = {
        "guided_evidence_executed": "true",
        "guided_evidence_ok": "true",
        "investigation_kind": "guided_evidence_collection",
        "service": str(row.get("service") or ""),
    }
    return GuidedEvidenceResult(
        ok=True,
        evidence=evidence,
        investigation_state=updated_state,
        meta=meta,
    )


def compose_guided_findings_summary(
    evidence: dict[str, Any],
    *,
    investigation_state: InvestigationState | None = None,
) -> list[str]:
    root = dict(evidence.get("root_cause") or {})
    correlation = dict(evidence.get("evidence_correlation") or {})
    lines: list[str] = []

    logs = list(evidence.get("logs") or [])
    if evidence.get("logs_available") and logs:
        lines.append(f"- Logs: collected **{len(logs)}** recent lines from Railway deployment/runtime sources.")
        summary = str(root.get("summary") or "").strip()
        if summary:
            lines.append(f"  - Signal: {summary}")
    else:
        checked = evidence.get("log_sources_checked") or []
        detail = f" Sources attempted: {', '.join(checked)}." if checked else ""
        lines.append(f"- Logs: unavailable from Railway right now.{detail}")

    events = list(evidence.get("events") or [])
    if evidence.get("events_available") and events:
        latest = events[0]
        state = str(latest.get("state") or "unknown")
        created = str(latest.get("created_at") or "—")
        message = str(latest.get("message") or f"Deployment {latest.get('id')} state={state}")
        lines.append(f"- Events: inspected **{len(events)}** Railway service events.")
        lines.append(f"  - Latest: `{created}` {message}")
    else:
        lines.append("- Events: service events were unavailable or empty from the current adapter.")

    correlation_lines = list(correlation.get("correlation_lines") or [])
    if correlation_lines:
        lines.append("- Correlation:")
        for item in correlation_lines[:4]:
            lines.append(f"  - {item}")
    elif correlation.get("conclusion"):
        lines.append(f"- Correlation: {correlation['conclusion']}")

    label = str(root.get("label") or "Unknown")
    category = str(root.get("category") or "unknown")
    confidence = str(root.get("confidence") or "low")
    lines.append(f"- Classification: **{label}** (`{category}`, confidence: {confidence}).")

    if investigation_state is not None:
        lines.append(
            f"- Investigation confidence: **{investigation_state.confidence_label}** "
            f"({investigation_state.confidence_score:.2f})."
        )
    elif correlation.get("confidence_note"):
        lines.append(f"- {correlation['confidence_note']}")

    return lines


def compose_guided_strategy_reply(
    *,
    opener_lines: list[str],
    evidence: dict[str, Any],
    investigation_state: InvestigationState | None,
    outcome: RepairAttemptOutcome | None,
    service: str,
) -> str:
    correlation = dict(evidence.get("evidence_correlation") or {})
    lines = list(opener_lines)
    lines.extend(
        [
            "",
            "I'm gathering deeper evidence now:",
        ]
    )
    for bullet in _GATHERING_BULLETS:
        lines.append(f"- {bullet}")

    lines.extend(["", "Findings:"])
    lines.extend(compose_guided_findings_summary(evidence, investigation_state=investigation_state))

    next_action = ""
    if investigation_state is not None and investigation_state.next_best_action:
        next_action = investigation_state.next_best_action
    elif correlation.get("best_next_step"):
        next_action = str(correlation["best_next_step"])

    if next_action:
        lines.extend(["", "Next best action:", next_action])
        reason = str(correlation.get("next_step_reason") or "").strip()
        if not reason and investigation_state is not None:
            reason_parts: list[str] = []
            if "fresh_wiredtiger_logs" in investigation_state.evidence:
                reason_parts.append("current logs are fresh but low-signal")
            if "stale_service_events" in investigation_state.evidence:
                reason_parts.append("service events were stale before this refresh")
            if "high_signal_logs" not in investigation_state.evidence:
                reason_parts.append("no fatal error or exit reason has been confirmed yet")
            if outcome is not None and not outcome.helped and outcome.result in {"regressed", "failed_after_mutation"}:
                reason_parts.append(f"the restart **{outcome.result.replace('_', ' ')}** without improving health")
            if reason_parts:
                reason = f"{' and '.join(reason_parts).capitalize()}."
        if reason:
            lines.extend(["", "Reason:", reason])

    if outcome is not None and not outcome.helped:
        lines.extend(
            [
                "",
                "I would not recommend another restart or redeploy until deeper failure evidence is collected.",
            ]
        )
    elif service:
        lines.extend(
            [
                "",
                f"I would not recommend another mutation on **{service}** until the failure evidence is stronger.",
            ]
        )

    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def try_enrich_strategy_with_guided_evidence(
    reply: str,
    *,
    session_id: str,
    state: InvestigationState | None,
    outcome: RepairAttemptOutcome | None,
    opener_lines: list[str] | None = None,
) -> tuple[str, dict[str, str]]:
    if not should_execute_guided_evidence(state=state, outcome=outcome):
        return reply, {}

    service = _service_label(state, outcome)
    if opener_lines is None:
        opener_lines = _default_opener_lines(reply, service=service, outcome=outcome)

    result = execute_guided_evidence_collection(session_id=session_id, state=state, outcome=outcome)
    if not result.ok or result.evidence is None:
        if result.error:
            return f"{reply}\n\n(Read-only evidence collection skipped: {result.error})", {}
        return reply, {}

    enriched = compose_guided_strategy_reply(
        opener_lines=opener_lines,
        evidence=result.evidence,
        investigation_state=result.investigation_state,
        outcome=outcome,
        service=service,
    )
    return enriched, dict(result.meta)


def _service_label(state: InvestigationState | None, outcome: RepairAttemptOutcome | None) -> str:
    if state is not None and state.service:
        return state.service
    if outcome is not None:
        return outcome.service or outcome.target.split("/")[-1].strip() or "the service"
    return "the service"


def _default_opener_lines(
    reply: str,
    *,
    service: str,
    outcome: RepairAttemptOutcome | None,
) -> list[str]:
    if outcome is not None and not outcome.helped:
        return [
            f"The **{service}** restart did not resolve the failure, so I would avoid another restart right now."
        ]
    first_block = reply.split("\n\n", 1)[0].strip()
    if first_block:
        return [first_block]
    return [f"Continuing the **{service}** investigation with deeper read-only evidence."]
