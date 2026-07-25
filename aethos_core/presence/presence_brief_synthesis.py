# SPDX-License-Identifier: Apache-2.0
"""Operator-grade brief synthesis."""

from __future__ import annotations

from typing import Any


def synthesize_operator_brief(
    *,
    window_hours: int,
    events: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    intent: str = "operational",
    focus: dict[str, Any] | None = None,
) -> str:
    """Produce concise, evidence-grounded operator brief."""
    focus_label = (focus or {}).get("mode") or intent
    visible = [e for e in events if str(e.get("priority") or "PASSIVE") != "PASSIVE"]
    incidents = [c for c in clusters if c.get("theme") not in ("internal_substrate", "general")]

    lines = [
        "**Operational brief**",
        "",
        f"Over the last {window_hours} hours, AethOS reviewed governed operational signals "
        f"(focus: {focus_label.replace('_', ' ')}).",
        "",
    ]

    if incidents:
        primary = incidents[0]
        lines.append(_narrative_for_cluster(primary, window_hours))
        if len(incidents) > 1:
            lines.append(f"Also detected: {incidents[1].get('title')} (confidence {incidents[1].get('confidence')}).")
    elif visible:
        lines.append(_narrative_for_events(visible[:3], intent))
    else:
        lines.append("No elevated operational incidents detected in the selected window.")

    lines.append("")
    lines.append(_confidence_assessment(incidents or visible))
    lines.append(_outage_assessment(incidents, visible))
    lines.append("")

    if recommendations:
        lines.append("**Recommended next steps (approval required):**")
        for rec in recommendations[:3]:
            lines.append(f"- {rec.get('title')}: {rec.get('suggested_action')}")
    else:
        lines.append("**Recommendations:** No new governed actions proposed — continue monitoring.")

    lines.extend(
        [
            "",
            "**Governance:** Readonly synthesis only — no autonomous mutation, deploy, or merge.",
        ]
    )
    return "\n".join(lines)


def _narrative_for_cluster(cluster: dict[str, Any], window_hours: int) -> str:
    theme = str(cluster.get("theme") or "")
    count = int(cluster.get("event_count") or 0)
    systems = ", ".join(cluster.get("related_systems") or [])
    if theme == "deployment_instability":
        return (
            f"Observed repeated deployment instability signals ({count} correlated events) "
            f"across {systems} in the last {window_hours}h."
        )
    if theme == "workflow_instability":
        return (
            f"GitHub workflow rerun instability detected ({count} correlated signals) "
            f"affecting {systems}."
        )
    return f"{cluster.get('title')} affecting {systems}."


def _narrative_for_events(events: list[dict[str, Any]], intent: str) -> str:
    summaries = [str(e.get("summary") or "") for e in events if e.get("summary")]
    if intent == "deployment":
        dep = [s for s in summaries if any(k in s.lower() for k in ("railway", "deployment", "workflow", "github"))]
        if dep:
            return f"Deployment-focused signals: {'; '.join(dep[:2])}."
    if summaries:
        return f"Notable signals: {'; '.join(summaries[:2])}."
    return "Limited elevated signals in window."


def _confidence_assessment(incidents_or_events: list[dict[str, Any]]) -> str:
    if not incidents_or_events:
        return "Confidence is low — insufficient correlated evidence."
    confs = [float(x.get("confidence") or x.get("attention_score") or 0.5) for x in incidents_or_events]
    avg = sum(confs) / len(confs)
    if avg >= 0.75:
        level = "high"
    elif avg >= 0.55:
        level = "moderate"
    else:
        level = "moderate-to-low due to incomplete provider telemetry"
    return f"Confidence is {level} (avg {avg:.2f})."


def _outage_assessment(incidents: list[dict[str, Any]], visible: list[dict[str, Any]]) -> str:
    critical = any(str(e.get("priority") or "") == "CRITICAL" for e in visible)
    if critical and incidents:
        return "Active production instability may require immediate human review."
    return "No active production outage detected from available governed evidence."
