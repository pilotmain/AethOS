# SPDX-License-Identifier: Apache-2.0
"""Evidence collection and diagnosis for failed Railway services."""

from __future__ import annotations

from typing import Any

from aethos_core.failed_service_investigation.failed_service_resolver import ResolvedFailedService
from aethos_core.failed_service_investigation.root_cause_classifier import classify_root_cause
from aethos_core.providers.railway.operations.logs_multisource import fetch_railway_logs_multisource


def _target_label(row: dict[str, Any]) -> str:
    return (
        f"{row.get('project', '—')} / {row.get('environment', '—')} / {row.get('service', '—')}"
    )


def collect_failed_service_evidence(target: ResolvedFailedService) -> dict[str, Any]:
    row = target.row
    service_name = str(row.get("service") or "")
    service_id = str(row.get("service_id") or "")
    deployment_state = str(row.get("deployment_state") or row.get("status") or "unknown")
    health = str(row.get("health") or "unknown")
    status = str(row.get("status") or "unknown")

    log_payload: dict[str, Any] = {"ok": False, "logs": [], "sources_checked": [], "errors": []}
    try:
        log_payload = fetch_railway_logs_multisource(
            service_name=service_name,
            service_id=service_id or None,
            limit=20,
            bypass_cache=True,
        )
    except Exception as exc:
        log_payload = {
            "ok": False,
            "logs": [],
            "sources_checked": [],
            "errors": [str(exc)],
            "all_sources_failed": True,
        }

    logs = list(log_payload.get("logs") or [])

    from aethos_core.providers.railway.operations.service_events_api import get_service_events

    events_payload = get_service_events(row, limit=20)
    events = list(events_payload.get("events") or [])

    root_cause = classify_root_cause(
        logs=logs,
        service_name=service_name,
        deployment_state=deployment_state,
        health_summary=f"status={status}; health={health}; deployment={deployment_state}",
    )

    evidence = {
        "target": row,
        "target_label": _target_label(row),
        "provider": target.provider,
        "deployment_state": deployment_state,
        "health": health,
        "status": status,
        "logs_available": bool(logs),
        "logs": logs[:20],
        "log_sources_checked": list(log_payload.get("sources_checked") or []),
        "log_errors": list(log_payload.get("errors") or []),
        "all_log_sources_failed": bool(log_payload.get("all_sources_failed")),
        "events_available": bool(events),
        "events": events[:20],
        "events_payload": events_payload,
        "root_cause": root_cause.to_dict(),
        "inventory_collected_at": row.get("inventory_collected_at") or row.get("collected_at"),
        "health_collected_at": row.get("health_collected_at") or row.get("inventory_collected_at"),
    }

    from aethos_core.evidence_correlation.correlated_diagnosis import correlate_evidence

    evidence["evidence_correlation"] = correlate_evidence(evidence).to_dict()
    return evidence


def compose_diagnosis_reply(evidence: dict[str, Any], *, investigation_state=None) -> str:
    row = evidence["target"]
    label = evidence["target_label"]
    root = dict(evidence.get("root_cause") or {})
    lines = [
        f"Diagnosis for **{label}**:",
        "",
        "Known state:",
        f"- Railway status: **{evidence.get('status', 'unknown')}**",
        f"- Deployment state: **{evidence.get('deployment_state', 'unknown')}**",
        f"- Logs available: **{'yes' if evidence.get('logs_available') else 'no'}**"
        + (f" ({len(evidence.get('logs') or [])} lines)" if evidence.get("logs_available") else ""),
    ]

    if evidence.get("logs_available"):
        checked = evidence.get("log_sources_checked") or []
        if checked:
            lines.append(f"- Sources checked: {', '.join(checked)}")
    else:
        checked = evidence.get("log_sources_checked") or []
        if checked:
            lines.append(f"- Sources attempted: {', '.join(checked)}")
        for err in evidence.get("log_errors") or []:
            lines.append(f"- Log fetch error: {err}")

    lines.extend(
        [
            "",
            "Classification:",
            f"- Category: **{root.get('label', 'Unknown')}** (`{root.get('category', 'unknown')}`)",
            f"- Confidence: **{root.get('confidence', 'low')}**",
            f"- Summary: {root.get('summary', 'Insufficient evidence')}",
        ]
    )

    interpretation = list(root.get("interpretation") or [])
    if interpretation:
        lines.extend(["", "Log interpretation:"])
        for item in interpretation:
            lines.append(f"- {item}")

    signals = list(root.get("log_signals") or [])
    if signals:
        lines.extend(["", "Log signals:"])
        for signal in signals[:5]:
            lines.append(f"- `{signal}`")

    gaps = list(root.get("evidence_gaps") or [])
    if gaps:
        lines.extend(["", "Evidence gaps:"])
        for gap in gaps:
            lines.append(f"- {gap}")

    correlation = dict(evidence.get("evidence_correlation") or {})
    if correlation:
        lines.extend(["", "Evidence correlation:"])
        for item in correlation.get("correlation_lines") or []:
            lines.append(item)
        if correlation.get("conclusion"):
            lines.extend(["", "Conclusion:", correlation["conclusion"]])
        if correlation.get("confidence_note"):
            lines.append("")
            lines.append(correlation["confidence_note"])
        if correlation.get("best_next_step"):
            lines.extend(["", "Best next step:", correlation["best_next_step"]])
            if correlation.get("next_step_reason"):
                lines.append(f"Reason: {correlation['next_step_reason']}")

    next_checks = list(root.get("next_checks") or [])
    if next_checks and not correlation.get("best_next_step"):
        lines.extend(["", "Most useful next checks:"])
        for idx, check in enumerate(next_checks, start=1):
            lines.append(f"{idx}. {check}")

    recommended = list(root.get("recommended_actions") or [])
    if recommended and not correlation.get("best_next_step"):
        lines.extend(["", "Recommended next action:"])
        for action in recommended[:3]:
            lines.append(f'- "{action}"')

    if root.get("bounded_diagnosis"):
        lines.extend(
            [
                "",
                "Note: This diagnosis is intentionally bounded — AethOS will not claim a final root cause "
                "without stronger evidence.",
            ]
        )

    if not root.get("suggests_mutation"):
        lines.extend(["", "No mutation recommended yet."])

    if investigation_state is not None and investigation_state.confidence_score < 0.6:
        lines.extend(
            [
                "",
                f"Investigation confidence remains **{investigation_state.confidence_label}** "
                f"({investigation_state.confidence_score:.2f}) — continuing evidence collection before mutation.",
            ]
        )

    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def compose_events_reply(evidence: dict[str, Any]) -> str:
    row = evidence["target"]
    label = evidence["target_label"]
    from aethos_core.providers.railway.operations.service_events_api import get_service_events

    events_payload = get_service_events(row, limit=20)
    lines = [
        f"I inspected Railway service events for **{label}**:",
        "",
        "Known state:",
        f"- Railway status: **{evidence.get('status', 'unknown')}**",
        f"- Deployment state: **{evidence.get('deployment_state', 'unknown')}**",
        "",
    ]

    events = list(events_payload.get("events") or [])
    if events_payload.get("ok") and events:
        lines.append("Events:")
        for event in events[:15]:
            state = event.get("state") or "unknown"
            created = event.get("created_at") or "—"
            message = event.get("message") or f"Deployment {event.get('id')} state={state}"
            lines.append(f"- `{created}` {message}")
            if event.get("error_message"):
                lines.append(f"  - error: {str(event.get('error_message'))[:240]}")
    elif events_payload.get("capability_gap"):
        lines.append(
            "Railway service events are not available from the current adapter yet. "
            "I can still use deployment state and logs, but event-level exit reason is missing."
        )
        err = str(events_payload.get("error") or "")
        if err:
            lines.append(f"- Adapter detail: {err}")
    else:
        lines.append("Railway service events were not available from the current provider adapter.")
        err = str(events_payload.get("error") or "")
        if err:
            lines.append(f"- Detail: {err}")
        lines.extend(
            [
                "",
                "Next checks:",
                "1. Fetch deployment/runtime logs around the failure timestamp",
                "2. Inspect deployment state in Railway",
                "3. Verify volume/env/config if startup failed",
            ]
        )

    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def compose_status_reply(evidence: dict[str, Any]) -> str:
    row = evidence["target"]
    label = evidence["target_label"]
    root = dict(evidence.get("root_cause") or {})
    lines = [
        f"Status for **{label}** from the last Railway provider-wide health report:",
        "",
        f"- Railway status: **{evidence.get('status', 'unknown')}**",
        f"- Health: **{evidence.get('health', 'unknown')}**",
        f"- Deployment state: **{evidence.get('deployment_state', 'unknown')}**",
        f"- Failure class: **{root.get('label', 'Unknown')}** (confidence: {root.get('confidence', 'low')})",
    ]
    if root.get("summary"):
        lines.append(f"- Summary: {root.get('summary')}")
    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def compose_logs_reply(evidence: dict[str, Any]) -> str:
    row = evidence["target"]
    label = evidence["target_label"]
    lines = [
        f"Checking logs for **{label}** from the last Railway provider-wide health report context.",
        "",
        f"Known state: status **{evidence.get('status', 'unknown')}**, deployment **{evidence.get('deployment_state', 'unknown')}**",
        "",
    ]
    logs = evidence.get("logs") or []
    if logs:
        lines.append("Recent log lines:")
        for entry in logs[:15]:
            ts = entry.get("timestamp") or entry.get("time") or "—"
            msg = entry.get("message") or entry.get("msg") or str(entry)
            lines.append(f"- `{ts}` {msg}")
    else:
        lines.append("Logs are unavailable from Railway API/runtime sources right now.")
        checked = evidence.get("log_sources_checked") or []
        if checked:
            lines.append(f"Sources attempted: {', '.join(checked)}")
        for err in evidence.get("log_errors") or []:
            lines.append(f"- {err}")
        lines.extend(
            [
                "",
                "Diagnostic next steps:",
                "1. Inspect latest deployment state/events in Railway",
                "2. Check build output if deployment never reached running",
                "3. Verify service env/config and dependency connectivity",
            ]
        )
    lines.append("")
    lines.append("No mutation has been performed.")
    return "\n".join(lines)
