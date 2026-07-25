# SPDX-License-Identifier: Apache-2.0
"""Compose cross-provider correlation replies."""

from __future__ import annotations

from typing import Any

from aethos_core.cross_provider_correlation.correlation_diagnosis import CorrelationDiagnosis
from aethos_core.cross_provider_correlation.correlation_graph import CorrelationGraph


def compose_correlation_reply(
    *,
    intent: str,
    diagnosis: CorrelationDiagnosis,
    graph: CorrelationGraph,
    snapshot: dict[str, Any],
) -> str:
    if intent == "failure_boundary":
        return compose_failure_boundary_reply(diagnosis=diagnosis, graph=graph)
    if intent == "runtime_reached":
        return compose_runtime_reached_reply(diagnosis=diagnosis, graph=graph)
    return compose_push_trace_reply(diagnosis=diagnosis, graph=graph, snapshot=snapshot)


def compose_push_trace_reply(
    *,
    diagnosis: CorrelationDiagnosis,
    graph: CorrelationGraph,
    snapshot: dict[str, Any],
) -> str:
    lines = ["I traced the latest push across providers.", ""]

    if graph.github:
        gh = graph.github
        lines.extend(
            [
                "GitHub:",
                f"- commit: `{gh.commit_sha[:12] or '—'}`",
                f"- repo: **{gh.repo or '—'}**",
                f"- branch: `{gh.branch or '—'}`",
                f"- workflows/checks: **{diagnosis.github_status}**",
            ]
        )
        workflow = dict((gh.metadata or {}).get("workflow_diagnostic") or {})
        latest = dict(workflow.get("latest_failed_run") or {})
        if latest.get("name"):
            lines.append(f"- latest workflow: **{latest.get('name')}** run #{latest.get('run_number')} → `{latest.get('conclusion') or 'failure'}`")
    else:
        lines.extend(["GitHub:", "- no correlated GitHub evidence in store"])

    lines.append("")
    if graph.vercel:
        ver = graph.vercel
        raw = dict(snapshot.get("raw", {}).get("vercel") or {})
        build = dict(raw.get("build_analysis") or ver.metadata.get("build_analysis") or {})
        lines.extend(
            [
                "Vercel:",
                f"- project: **{ver.project or '—'}**",
                f"- deployment: `{ver.deployment_id[:12] or '—'}`",
                f"- status: **{diagnosis.vercel_status}**",
                f"- commit: `{ver.commit_sha[:12] or '—'}`",
            ]
        )
        for err in build.get("error_lines") or []:
            lines.append(f"- build logs: `{str(err)[:160]}`")
        domain = dict(ver.metadata.get("domain_health") or raw.get("domain_health") or {})
        if domain.get("summary"):
            lines.append(f"- domain health: {domain['summary']}")
    else:
        lines.extend(["Vercel:", "- no correlated Vercel deployment evidence"])

    lines.append("")
    if graph.railway:
        rw = graph.railway
        lines.extend(
            [
                "Railway:",
                f"- service: **{rw.project}/{rw.service}**",
                f"- runtime: **{diagnosis.railway_status}**",
                f"- commit: `{rw.commit_sha[:12] or '—'}`",
            ]
        )
    else:
        lines.extend(["Railway:", "- no correlated Railway runtime evidence"])

    lines.extend(["", "Conclusion:", diagnosis.conclusion])
    if diagnosis.needs_binding:
        lines.extend(
            [
                "",
                "Next step:",
                "Add or refresh provider source bindings so GitHub repo, Vercel project, and Railway service correlate on the same commit.",
            ]
        )
    else:
        lines.extend(["", "Next readonly evidence step:", _next_step(diagnosis)])
    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def compose_failure_boundary_reply(*, diagnosis: CorrelationDiagnosis, graph: CorrelationGraph) -> str:
    lines = [
        "Cross-provider failure boundary:",
        "",
        f"**{diagnosis.failure_boundary}**",
        "",
        diagnosis.conclusion,
        "",
    ]
    for item in diagnosis.lines:
        lines.append(f"- {item}")
    if diagnosis.failure_boundary == "vercel":
        lines.extend(
            [
                "",
                "Interpretation:",
                "GitHub CI is not the current blocker — inspect Vercel build logs and deployment metadata for the correlated commit.",
            ]
        )
    elif diagnosis.failure_boundary == "github":
        lines.extend(
            [
                "",
                "Interpretation:",
                "Downstream deploy should be treated as blocked until GitHub workflow/check evidence is green.",
            ]
        )
    elif diagnosis.failure_boundary == "railway":
        lines.extend(
            [
                "",
                "Interpretation:",
                "Deploy likely reached runtime — inspect Railway logs and service health for the correlated revision.",
            ]
        )
    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def compose_runtime_reached_reply(*, diagnosis: CorrelationDiagnosis, graph: CorrelationGraph) -> str:
    reached = diagnosis.vercel_status == "ready" or diagnosis.railway_status in {"healthy", "failed", "unhealthy", "crashed", "error"}
    lines = [
        "Deployment runtime correlation:",
        "",
        f"- GitHub: **{diagnosis.github_status}**",
        f"- Vercel: **{diagnosis.vercel_status}**",
        f"- Railway: **{diagnosis.railway_status}**",
        "",
    ]
    if reached and graph.railway:
        lines.append("Deployment evidence reached Railway runtime scope for the correlated commit.")
    elif diagnosis.vercel_status == "ready":
        lines.append("Deployment reached Vercel successfully; Railway runtime evidence is not correlated yet.")
    elif diagnosis.vercel_status == "failed":
        lines.append("Deployment did not reach healthy runtime — Vercel build/deploy failed first.")
    elif diagnosis.github_status == "failed":
        lines.append("Deployment likely never propagated — GitHub CI failed before deploy.")
    else:
        lines.append("Runtime reach is inconclusive — add source bindings and refresh provider diagnostics.")
    lines.extend(["", "Conclusion:", diagnosis.conclusion, "", "No mutation has been performed."])
    return "\n".join(lines)


def compose_correlation_summary_lines(diagnosis: CorrelationDiagnosis, graph: CorrelationGraph) -> list[str]:
    lines = [f"Failure boundary: **{diagnosis.failure_boundary}** ({diagnosis.confidence} confidence)"]
    lines.extend(diagnosis.lines)
    if graph.matched_commit:
        lines.append(f"Correlated commit `{graph.matched_commit[:12]}` across {len(graph.links)} link(s).")
    return lines


def _next_step(diagnosis: CorrelationDiagnosis) -> str:
    if diagnosis.failure_boundary == "github":
        return "Inspect failing GitHub workflow/check logs, then rerun readonly Vercel diagnostics after CI is green."
    if diagnosis.failure_boundary == "vercel":
        return "Read Vercel build logs for the correlated deployment commit, then verify domain health."
    if diagnosis.failure_boundary == "railway":
        return "Inspect Railway runtime logs and service health for the deployment revision tied to the correlated commit."
    return "Refresh GitHub, Vercel, and Railway readonly diagnostics for the same repo/project/service binding."
