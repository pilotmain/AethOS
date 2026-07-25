# SPDX-License-Identifier: Apache-2.0
"""Cross-provider failure boundary diagnosis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.cross_provider_correlation.correlation_graph import CorrelationGraph


@dataclass
class CorrelationDiagnosis:
    failure_boundary: str = "unknown"
    confidence: str = "low"
    conclusion: str = ""
    github_status: str = "unknown"
    vercel_status: str = "unknown"
    railway_status: str = "unknown"
    lines: list[str] = field(default_factory=list)
    needs_binding: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_boundary": self.failure_boundary,
            "confidence": self.confidence,
            "conclusion": self.conclusion,
            "github_status": self.github_status,
            "vercel_status": self.vercel_status,
            "railway_status": self.railway_status,
            "lines": list(self.lines),
            "needs_binding": self.needs_binding,
        }


def diagnose_correlation_graph(graph: CorrelationGraph, *, snapshot: dict[str, Any] | None = None) -> CorrelationDiagnosis:
    github_status = _github_status(graph)
    vercel_status = _vercel_status(graph, snapshot=snapshot)
    railway_status = _railway_status(graph)

    diagnosis = CorrelationDiagnosis(
        github_status=github_status,
        vercel_status=vercel_status,
        railway_status=railway_status,
        confidence=graph.confidence,
    )

    github_failed = github_status == "failed"
    github_passed = github_status == "passed"
    vercel_failed = vercel_status == "failed"
    vercel_ready = vercel_status == "ready"
    vercel_missing = vercel_status in {"missing", "unknown"} and graph.vercel is None
    railway_failed = railway_status in {"failed", "unhealthy", "crashed", "error"}
    railway_healthy = railway_status in {"healthy", "ready", "passed", "ok"}

    if not graph.links:
        if github_failed and (vercel_missing or not graph.vercel):
            diagnosis.failure_boundary = "github"
            diagnosis.needs_binding = True
            diagnosis.conclusion = "GitHub CI failed before a matching Vercel deployment was observed — failure boundary is GitHub."
            diagnosis.lines.append("No Vercel deployment matched the failed GitHub commit yet.")
            return diagnosis
        if not graph.github and not graph.vercel and not graph.railway:
            diagnosis.failure_boundary = "unknown"
            diagnosis.needs_binding = True
            diagnosis.conclusion = "No cross-provider evidence is available yet — run GitHub/Vercel/Railway readonly diagnostics or add source bindings."
            diagnosis.lines.append("No provider evidence published to the correlation store.")
            return diagnosis
        diagnosis.failure_boundary = "unknown"
        diagnosis.needs_binding = True
        diagnosis.conclusion = "Provider evidence exists but could not be correlated — add or refresh source bindings between GitHub repo, Vercel project, and Railway service."
        diagnosis.lines.append("No commit/repo/binding match found across providers.")
        return diagnosis

    if github_failed and (vercel_missing or not graph.vercel):
        diagnosis.failure_boundary = "github"
        diagnosis.conclusion = "GitHub CI failed before a matching Vercel deployment was observed — failure boundary is GitHub."
    elif github_failed and vercel_failed:
        diagnosis.failure_boundary = "github"
        diagnosis.conclusion = "GitHub workflow/check failures align with downstream deploy failure — start at GitHub CI, then verify Vercel consumed the failing commit."
    elif github_passed and vercel_failed:
        diagnosis.failure_boundary = "vercel"
        diagnosis.conclusion = "The GitHub workflow passed, but the Vercel deployment failed during build/deploy — failure is currently isolated to Vercel."
    elif github_passed and vercel_ready and railway_failed:
        diagnosis.failure_boundary = "railway"
        diagnosis.conclusion = "GitHub and Vercel look healthy for the correlated commit — runtime failure is isolated to Railway."
    elif github_passed and vercel_ready and railway_healthy:
        diagnosis.failure_boundary = "none"
        diagnosis.conclusion = "GitHub, Vercel, and Railway evidence are healthy on the correlated commit surface."
    elif vercel_failed:
        diagnosis.failure_boundary = "vercel"
        diagnosis.conclusion = "Vercel deployment evidence shows failure on the correlated surface."
    elif github_failed:
        diagnosis.failure_boundary = "github"
        diagnosis.conclusion = "GitHub evidence shows CI failure on the correlated commit."
    elif railway_failed:
        diagnosis.failure_boundary = "railway"
        diagnosis.conclusion = "Railway runtime evidence shows failure after deploy propagation."
    else:
        diagnosis.failure_boundary = "unknown"
        diagnosis.conclusion = "Correlated evidence is mixed — inspect the next readonly step per provider."

    diagnosis.lines.extend(_diagnosis_lines(graph, diagnosis))
    graph.failure_boundary = diagnosis.failure_boundary
    return diagnosis


def _github_status(graph: CorrelationGraph) -> str:
    if not graph.github:
        return "missing"
    status = str(graph.github.status or "unknown").lower()
    if status in {"failed", "passed"}:
        return status
    workflow = dict((graph.github.metadata or {}).get("workflow_diagnostic") or {})
    checks = dict((graph.github.metadata or {}).get("checks") or {})
    if workflow.get("latest_failed_run") or checks.get("failed_count"):
        return "failed"
    if workflow.get("ok") or checks.get("ok"):
        return "passed"
    return status or "unknown"


def _vercel_status(graph: CorrelationGraph, *, snapshot: dict[str, Any] | None = None) -> str:
    if not graph.vercel:
        return "missing"
    status = str(graph.vercel.status or "unknown").lower()
    raw = dict((snapshot or {}).get("raw", {}).get("vercel") or {})
    build = dict(raw.get("build_analysis") or graph.vercel.metadata.get("build_analysis") or {})
    if status in {"failed", "error", "canceled"} or build.get("error_lines"):
        return "failed"
    if status in {"ready", "completed"}:
        return "ready"
    return status or "unknown"


def _railway_status(graph: CorrelationGraph) -> str:
    if not graph.railway:
        return "missing"
    status = str(graph.railway.status or "unknown").lower()
    if status in {"failed", "crashed", "error", "unhealthy"}:
        return "failed"
    if status in {"healthy", "ready", "ok", "running"}:
        return "healthy"
    return status or "unknown"


def _diagnosis_lines(graph: CorrelationGraph, diagnosis: CorrelationDiagnosis) -> list[str]:
    lines: list[str] = []
    if graph.github:
        lines.append(f"GitHub status: **{diagnosis.github_status}** on `{graph.github.repo}` commit `{graph.github.commit_sha[:12] or '—'}`")
    if graph.vercel:
        lines.append(
            f"Vercel status: **{diagnosis.vercel_status}** for project `{graph.vercel.project}` deployment `{graph.vercel.deployment_id[:12] or '—'}`"
        )
    if graph.railway:
        lines.append(
            f"Railway status: **{diagnosis.railway_status}** for `{graph.railway.project}/{graph.railway.service}`"
        )
    if graph.matched_commit:
        lines.append(f"Matched commit: `{graph.matched_commit[:12]}`")
    return lines
