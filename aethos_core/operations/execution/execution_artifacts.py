# SPDX-License-Identifier: Apache-2.0
"""Structured read-only execution artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass
class ExecutionArtifact:
    execution_id: str
    provider: str
    operation_type: str
    target_name: str | None
    read_only: bool = True
    mutating: bool = False
    approved_actions: list[str] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    timeline: list[dict[str, Any]] = field(default_factory=list)
    confidence: str = "possible"
    probable_root_cause: str | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    operational_events: list[dict[str, Any]] = field(default_factory=list)
    diagnostic: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time)
    auth_method: str = ""
    auth_method_label: str = ""
    data_source: str = "memory"

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "provider": self.provider,
            "operation_type": self.operation_type,
            "target_name": self.target_name,
            "read_only": self.read_only,
            "mutating": self.mutating,
            "approved_actions": list(self.approved_actions),
            "findings": list(self.findings),
            "timeline": list(self.timeline),
            "confidence": self.confidence,
            "probable_root_cause": self.probable_root_cause,
            "evidence": list(self.evidence),
            "operational_events": list(self.operational_events),
            "diagnostic": dict(self.diagnostic),
            "created_at": self.created_at,
            "auth_method": self.auth_method,
            "auth_method_label": self.auth_method_label,
            "data_source": self.data_source,
        }


def _format_evidence_tier_lines(items: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for item in items:
        conf = str(item.get("confidence", "possible")).replace("_", " ")
        msg = item.get("message", "")
        lines.append(f"- **[{conf}]** {msg}")
    return lines


def _format_deployment_block(title: str, dep: dict[str, Any]) -> list[str]:
    if not dep:
        return [f"*(none)*"]
    lines = [
        f"- **ID:** `{dep.get('id', '')[:16]}`",
        f"- **State:** {dep.get('state', 'unknown')}",
        f"- **Target:** {dep.get('target', 'unknown')}",
    ]
    if dep.get("branch"):
        lines.append(f"- **Branch:** `{dep.get('branch')}`")
    if dep.get("commit"):
        lines.append(f"- **Commit:** `{dep.get('commit')}`")
    label = dep.get("created_at_label") or dep.get("created_at")
    if label:
        lines.append(f"- **Created:** {label}")
    if dep.get("error_message"):
        lines.append(f"- **Error:** {dep.get('error_message')}")
    if dep.get("commit_message"):
        lines.append(f"- **Message:** {dep.get('commit_message')}")
    return lines


def format_failure_diagnostic_report(artifact: ExecutionArtifact) -> str:
    from aethos_core.operations.execution.execution_formatting import format_timestamp

    diag = artifact.diagnostic or {}
    source_label = {
        "provider_api": "Provider API execution",
        "browser_fallback": "Browser fallback used for missing provider API data",
        "memory": "Operational memory",
    }.get(artifact.data_source, artifact.data_source or "unknown")

    failure_conf = str(diag.get("failure_reason_confidence") or artifact.confidence).replace("_", " ")
    impact_conf = str(diag.get("production_impact_confidence") or "insufficient_evidence").replace("_", " ")

    lines = [
        "# Read-only execution report",
        "",
        "## Summary",
        "",
        f"- **Provider:** {artifact.provider}",
        f"- **Operation:** {artifact.operation_type}",
        f"- **Target:** `{artifact.target_name or '(none)'}`",
        f"- **Auth method:** {artifact.auth_method_label or artifact.auth_method or 'unknown'}",
        f"- **Data source:** {source_label}",
        f"- **Read-only:** yes · **No mutation performed**",
        f"- **Failure reason confidence:** {failure_conf}",
        f"- **Production impact confidence:** {impact_conf}",
        "",
        "## Primary finding",
        "",
        str(diag.get("primary_finding") or artifact.probable_root_cause or "(none)"),
        "",
        "## Production impact",
        "",
        str(diag.get("production_impact_summary") or "Unknown"),
        "",
        "## Most relevant failed deployment",
        "",
        *_format_deployment_block("failed", diag.get("failed_deployment") or {}),
        "",
        "## Last successful production deployment",
        "",
        *_format_deployment_block("success", diag.get("last_successful_production_deployment") or {}),
        "",
        "## Operational timeline",
        "",
    ]
    for ev in artifact.operational_events:
        at = format_timestamp(ev.get("at")) or ""
        prefix = f"{at} · " if at else ""
        lines.append(f"- {prefix}{ev.get('label', 'event')} ({ev.get('source', 'unknown')})")
    if not artifact.operational_events:
        lines.append("- (none)")

    tiers = (diag.get("evidence_by_tier") or {}) if isinstance(diag.get("evidence_by_tier"), dict) else {}
    for tier_title, key in (
        ("Primary evidence", "primary"),
        ("Supporting context", "supporting"),
        ("Historical context", "historical"),
    ):
        tier_items = tiers.get(key) if isinstance(tiers.get(key), list) else []
        if tier_items:
            lines.extend(["", f"## {tier_title}", ""])
            lines.extend(_format_evidence_tier_lines(tier_items))

    debug_items = tiers.get("debug") if isinstance(tiers.get("debug"), list) else []
    if debug_items:
        lines.extend(["", "## Debug evidence (all deployment records)", ""])
        lines.extend(_format_evidence_tier_lines(debug_items[:12]))
        if len(debug_items) > 12:
            lines.append(f"- … and {len(debug_items) - 12} more debug record(s) in artifact JSON")

    next_checks = diag.get("next_safe_checks") or []
    if next_checks:
        lines.extend(["", "## Next safe checks", ""])
        for step in next_checks:
            lines.append(f"- {step}")

    if artifact.probable_root_cause:
        lines.extend(["", "## Actionable diagnosis", "", artifact.probable_root_cause])

    lines.extend(["", "## Execution timeline", ""])
    for ev in artifact.timeline:
        lines.append(f"- {ev.get('status', 'event')}: {ev.get('message', '')}")

    return "\n".join(lines).strip()


def format_execution_report(artifact: ExecutionArtifact) -> str:
    if artifact.operation_type in ("why_down", "inspect_failed_deployment") and artifact.diagnostic:
        return format_failure_diagnostic_report(artifact)

    from aethos_core.operations.execution.execution_formatting import format_timestamp

    source_label = {
        "provider_api": "Provider API execution",
        "browser_fallback": "Browser fallback used for missing provider API data",
        "memory": "Operational memory",
    }.get(artifact.data_source, artifact.data_source or "unknown")
    confidence_label = artifact.confidence.replace("_", " ")
    lines = [
        "# Read-only execution report",
        "",
        f"- **Provider:** {artifact.provider}",
        f"- **Operation:** {artifact.operation_type}",
        f"- **Target:** `{artifact.target_name or '(none)'}`",
        f"- **Auth method:** {artifact.auth_method_label or artifact.auth_method or 'unknown'}",
        f"- **Data source:** {source_label}",
        f"- **Read-only:** yes · **No mutation performed**",
        f"- **Confidence:** {confidence_label}",
        "",
        "## Timeline",
        "",
    ]
    for ev in artifact.timeline:
        lines.append(f"- {ev.get('status', 'event')}: {ev.get('message', '')}")
    if artifact.operational_events:
        lines.extend(["", "## Operational events", ""])
        for ev in artifact.operational_events:
            at = format_timestamp(ev.get("at")) or ""
            prefix = f"{at} · " if at else ""
            lines.append(f"- {prefix}{ev.get('label', 'event')} ({ev.get('source', 'unknown')})")
    if artifact.evidence:
        lines.extend(["", "## Evidence", ""])
        for item in artifact.evidence:
            src = item.get("source", "unknown")
            typ = item.get("type", "signal")
            conf = str(item.get("confidence", "possible")).replace("_", " ")
            msg = item.get("message", "")
            lines.append(f"- **[{conf}]** `{src}` · {typ}: {msg}")
    lines.extend(["", "## Findings", ""])
    for f in artifact.findings:
        title = f.get("action") or f.get("kind") or "finding"
        source = f.get("source")
        lines.append(f"### {title}" + (f" ({source})" if source else ""))
        body = str(f.get("output") or f.get("summary") or "")
        lines.append(body[:4000] if body else "(empty)")
        lines.append("")
    if artifact.probable_root_cause:
        lines.extend(["## Probable root cause", "", artifact.probable_root_cause, ""])
    return "\n".join(lines).strip()
