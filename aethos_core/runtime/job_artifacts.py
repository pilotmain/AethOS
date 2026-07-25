# SPDX-License-Identifier: Apache-2.0
"""Artifact shape — summary for chat, full report for Mission Control."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.runtime.job_types import (
    uses_external,
    uses_github_readonly,
    uses_operation_preflight,
    uses_provider,
    uses_railway_readonly,
    uses_readonly_execution,
    uses_vercel_readonly,
)


@dataclass
class JobArtifactBundle:
    full_result: str
    summary: str
    preview: str


def _first_line(text: str, max_len: int = 200) -> str:
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("⚠️"):
            continue
        return line[:max_len]
    return ""


def _strip_fallback_header(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].strip().startswith("⚠️ Provider unavailable"):
        return "\n".join(lines[1:]).strip()
    return text.strip()


def _extract_bullet_items(body: str, *, max_items: int = 5) -> list[str]:
    items: list[str] = []
    for line in body.splitlines():
        raw = line.strip()
        if not raw:
            continue
        if raw.startswith("- [ ]") or raw.startswith("- [x]") or raw.startswith("- [X]"):
            items.append(raw[5:].strip()[:140])
        elif raw.startswith(("- ", "* ")):
            items.append(raw[2:].strip()[:140])
        elif raw.startswith("## "):
            items.append(raw[3:].strip()[:140])
        elif raw.startswith("# "):
            items.append(raw[2:].strip()[:140])
        if len(items) >= max_items:
            break
    if items:
        return items[:max_items]

    plain = [
        ln.strip()
        for ln in body.splitlines()
        if ln.strip() and not ln.strip().startswith("#") and not ln.strip().startswith("⚠️")
    ]
    return [ln[:140] for ln in plain[:max_items]]


def _generic_summary_bullets(job_type: str, body: str) -> list[str]:
    items = _extract_bullet_items(body, max_items=4)
    if len(items) >= 2:
        return items
    if job_type == "comparison_brief":
        return [
            "Competitor landscape captured",
            "Positioning and tradeoffs noted",
            "Recommendations included in full report",
        ]
    if job_type == "roadmap_generation":
        return [
            "MVP phases outlined",
            "Test-gated milestones listed",
            "Full roadmap in Mission Control",
        ]
    if job_type == "checklist_generation":
        return [
            "Checklist items generated",
            "Open Mission Control for full checklist",
        ]
    if job_type == "external_health_report":
        return [
            "Public status source checked",
            "CLI availability noted (approval required to run commands)",
            "Full report in Mission Control → Jobs",
        ]
    if uses_readonly_execution(job_type):
        items = _extract_bullet_items(body, max_items=6)
        if items:
            return items
        return [
            "Approved read-only execution completed",
            "Findings in Mission Control → Jobs",
        ]
    if uses_operation_preflight(job_type):
        items = _extract_bullet_items(body, max_items=6)
        if items:
            return items
        return [
            "Read-only operation preflight completed",
            "Approve read-only execution in Mission Control when ready",
            "Full preflight report in Mission Control → Jobs",
        ]
    if uses_vercel_readonly(job_type):
        items = _extract_bullet_items(body, max_items=8)
        if items:
            return items
        return [
            "Read-only browser inspection completed",
            "See summary bullets above",
            "Full excerpt in Mission Control → Jobs",
        ]
    if uses_railway_readonly(job_type):
        items = _extract_bullet_items(body, max_items=8)
        if items:
            return items
        return [
            "Railway services inventory completed",
            "See summary above",
            "Full report in Mission Control → Jobs",
        ]
    if uses_github_readonly(job_type):
        items = _extract_bullet_items(body, max_items=8)
        if items:
            return items
        return [
            "GitHub repositories inventory completed",
            "See summary above",
            "Full report in Mission Control → Jobs",
        ]
    return [
        "Work completed successfully",
        "Details captured in full report",
    ]


def build_artifact_bundle(full_text: str, *, job_type: str, title: str) -> JobArtifactBundle:
    """Split full provider/local output into chat summary vs MC artifact."""
    full_result = (full_text or "").strip()
    body = _strip_fallback_header(full_result)
    preview = _first_line(body, 200) or _first_line(full_result, 200) or title[:200]

    items = _generic_summary_bullets(job_type, body)
    summary_lines = [f"- {item}" for item in items[:5]]
    if uses_provider(job_type):
        summary_lines.append("- Open Mission Control → Jobs for the full report")
    summary = "\n".join(summary_lines)

    return JobArtifactBundle(
        full_result=full_result,
        summary=summary,
        preview=preview,
    )


def completion_headline(job_type: str, title: str) -> str:
    if job_type == "comparison_brief":
        return "competitor brief ready"
    if job_type == "roadmap_generation":
        return "roadmap ready"
    if job_type == "architecture_summary":
        return "architecture summary ready"
    if job_type == "planning_document":
        return "planning document ready"
    if job_type == "research_plan":
        return "research plan ready"
    if job_type == "checklist_generation":
        return "checklist ready"
    if job_type == "external_health_report":
        return "Vercel health report ready"
    if uses_readonly_execution(job_type):
        return "read-only execution complete"
    if uses_operation_preflight(job_type):
        return "operation preflight ready — approval required"
    if uses_vercel_readonly(job_type):
        return "Vercel read-only inspection complete"
    if uses_railway_readonly(job_type):
        return "Railway services inventory ready"
    if uses_github_readonly(job_type):
        return "GitHub repositories inventory ready"
    return f"{title} ready" if title else "work ready"


def started_event_message(job_type: str, title: str) -> str:
    if job_type == "comparison_brief":
        return f"⏳ Job started — researching competitors"
    if job_type == "roadmap_generation":
        return f"⏳ Job started — {title or 'organizing roadmap'}"
    if job_type == "architecture_summary":
        return f"⏳ Job started — drafting architecture summary"
    if job_type == "planning_document":
        return f"⏳ Job started — {title or 'drafting planning document'}"
    if job_type == "research_plan":
        return f"⏳ Job started — {title or 'researching'}"
    if uses_railway_readonly(job_type):
        return "⏳ Job started — Railway services inventory"
    if uses_github_readonly(job_type):
        return "⏳ Job started — GitHub repositories inventory"
    return f"⏳ Job started — {title}"


def _readonly_execution_completion_copy(
    *,
    operation_type: str,
    target_name: str,
    readonly_execution: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    op = (operation_type or "execution").replace("_", " ")
    target = target_name or "(unknown)"
    head = f"✅ Read-only execution completed — {op} for `{target}`"
    bullets: list[str] = []
    artifact = readonly_execution or {}
    evidence = artifact.get("evidence") if isinstance(artifact.get("evidence"), list) else []
    op_events = artifact.get("operational_events") if isinstance(artifact.get("operational_events"), list) else []
    confidence = str(artifact.get("confidence") or "").replace("_", " ")
    data_source = str(artifact.get("data_source") or "")

    if operation_type == "list_domains":
        domain_count = sum(1 for e in evidence if isinstance(e, dict) and e.get("type") == "domain_record")
        bullets.append(f"Found {domain_count or 'no'} domain record(s) via provider API.")
    elif operation_type == "list_deployments":
        bullets.append("Recent deployment states captured from provider API.")
    elif operation_type == "project_details":
        bullets.append("Project metadata captured from provider API.")
    elif operation_type in ("why_down", "inspect_failed_deployment"):
        diag = artifact.get("diagnostic") if isinstance(artifact.get("diagnostic"), dict) else {}
        failure_conf = str(diag.get("failure_reason_confidence") or artifact.get("confidence") or "").replace("_", " ")
        if failure_conf:
            bullets.append(f"Failure confidence: {failure_conf}.")
        impact = str(diag.get("production_impact_summary") or "").strip()
        if impact:
            bullets.append(f"Production impact: {impact[:180]}")
        elif artifact.get("probable_root_cause"):
            bullets.append(str(artifact["probable_root_cause"])[:200])
        primary = str(diag.get("primary_finding") or "").strip()
        if primary and primary not in " ".join(bullets):
            bullets.append(primary[:200])
    elif evidence:
        bullets.append(f"Collected {len(evidence)} evidence item(s).")

    if data_source == "provider_api":
        bullets.append("Source: Provider API · no browser required.")
    elif data_source == "browser_fallback":
        bullets.append("Browser fallback used for missing provider API data.")
    if op_events:
        bullets.append(f"Operational timeline: {len(op_events)} event(s).")
    bullets.append("Open Mission Control → Jobs → Read-only executions for full evidence.")
    return head, bullets


def chat_completion_event_message(
    job_type: str,
    title: str,
    summary: str,
    *,
    fallback: bool,
    preflight_status: str = "",
    auth_method: str | None = None,
    operation_type: str = "",
    target_name: str = "",
    readonly_execution: dict[str, Any] | None = None,
) -> str:
    """Chat-safe completion copy — never the full markdown artifact."""
    from aethos_core.connections.adapters import (
        github_inspection_completion_message,
        railway_inspection_completion_message,
        vercel_inspection_completion_message,
    )

    head = f"✅ Job completed — {completion_headline(job_type, title)}"
    parts = [head]
    if summary.strip():
        parts.append("")
        parts.append("Summary:")
        parts.append(summary.strip())
    if fallback:
        parts.append("")
        parts.append("(Template fallback — enable Anthropic in Settings for live research.)")
    if uses_readonly_execution(job_type):
        head, bullets = _readonly_execution_completion_copy(
            operation_type=operation_type,
            target_name=target_name,
            readonly_execution=readonly_execution,
        )
        parts = [head, "", "Summary:"]
        parts.extend(f"- {b}" for b in bullets)
        parts.append("")
        parts.append("Approved read-only execution — no mutations were performed.")
        return "\n".join(parts)
    elif uses_operation_preflight(job_type):
        parts.append("")
        if preflight_status == "blocked":
            parts.append("Execution is currently blocked until browser runtime is healthy.")
        else:
            parts.append("Read-only preflight only — approve execution in Mission Control when ready.")
        parts.append("Open Mission Control → Jobs for the full preflight report.")
    elif uses_vercel_readonly(job_type):
        parts.append("")
        parts.append(vercel_inspection_completion_message(auth_method))
        parts.append("Open Mission Control → Jobs for the full report.")
    elif uses_railway_readonly(job_type):
        parts.append("")
        parts.append(railway_inspection_completion_message(auth_method))
        parts.append("Open Mission Control → Jobs for the full report.")
    elif uses_github_readonly(job_type):
        parts.append("")
        parts.append(github_inspection_completion_message(auth_method))
        parts.append("Open Mission Control → Jobs for the full report.")
    elif uses_provider(job_type) or uses_external(job_type):
        parts.append("")
        parts.append("Open Mission Control → Jobs for the full report.")
    return "\n".join(parts)
