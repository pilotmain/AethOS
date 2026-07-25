# SPDX-License-Identifier: Apache-2.0
"""Publish provider diagnostics into the shared correlation store."""

from __future__ import annotations

from typing import Any

from aethos_core.cross_provider_correlation.correlation_runtime import build_correlation_state
from aethos_core.cross_provider_correlation.correlation_store import (
    publish_github_evidence,
    publish_railway_health_rows,
    publish_vercel_evidence,
)


def ingest_github_live_evidence(session_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
    publish_github_evidence(session_id, evidence)
    publish_railway_health_rows(session_id)
    state = build_correlation_state(session_id=session_id)
    return {
        "lines": _summary_lines(state),
        "failure_boundary": state["cross_provider_correlation"]["failure_boundary"],
        "confidence": state["cross_provider_correlation"]["confidence"],
        "deploy_related_failures": 1 if state["cross_provider_correlation"]["failure_boundary"] not in {"none", "unknown"} else 0,
    }


def ingest_vercel_live_evidence(session_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
    publish_vercel_evidence(session_id, evidence)
    publish_railway_health_rows(session_id)
    state = build_correlation_state(session_id=session_id)
    github_lines = _github_lines_from_state(state)
    return {
        "ok": True,
        "available": bool(github_lines),
        "lines": github_lines,
        "evidence": state.get("graph", {}).get("github"),
        "failure_boundary": state["cross_provider_correlation"]["failure_boundary"],
        "confidence": state["cross_provider_correlation"]["confidence"],
    }


def _summary_lines(state: dict[str, Any]) -> list[str]:
    corr = dict(state.get("cross_provider_correlation") or {})
    lines: list[str] = []
    if corr.get("conclusion"):
        lines.append(str(corr["conclusion"]))
    if corr.get("vercel_project"):
        lines.append(f"Vercel project **{corr['vercel_project']}** correlated on commit `{str(corr.get('matched_commit') or '—')[:12]}`.")
    if corr.get("railway_service"):
        lines.append(f"Railway runtime **{corr['railway_service']}** included in correlation graph.")
    if corr.get("failure_boundary") and corr.get("failure_boundary") != "unknown":
        lines.append(f"Current failure boundary: **{corr['failure_boundary']}** ({corr.get('confidence')} confidence).")
    if not lines:
        lines.append("No cross-provider deployment correlation yet — inspect Vercel/Railway readonly diagnostics for the same commit.")
    return lines


def _github_lines_from_state(state: dict[str, Any]) -> list[str]:
    corr = dict(state.get("cross_provider_correlation") or {})
    lines: list[str] = []
    gh = dict((state.get("graph") or {}).get("github") or {})
    if not gh:
        lines.append("GitHub evidence unavailable in correlation store — run GitHub readonly diagnostics or add a GitHub API token.")
        return lines
    status = str(gh.get("status") or "unknown")
    lines.append(f"GitHub repo **{gh.get('repo') or '—'}** is **{status}** on commit `{str(gh.get('commit_sha') or '—')[:12]}`.")
    if corr.get("failure_boundary") == "github":
        lines.append("Correlation boundary currently points to GitHub CI before Vercel deploy.")
    elif corr.get("failure_boundary") == "vercel":
        lines.append("GitHub CI is green on correlated evidence — inspect Vercel build/deploy failure next.")
    return lines
