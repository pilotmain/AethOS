# SPDX-License-Identifier: Apache-2.0
"""Backward-compatible Vercel GitHub correlation wrapper."""

from __future__ import annotations

from typing import Any

from aethos_core.cross_provider_correlation.correlation_runtime import build_correlation_state
from aethos_core.cross_provider_correlation.correlation_store import publish_vercel_evidence


def correlate_github_source(
    *,
    repository: str,
    commit_sha: str = "",
    session_id: str = "default",
    github_token: str | None = None,
) -> dict[str, Any]:
    _ = github_token
    if repository and commit_sha:
        publish_vercel_evidence(
            session_id,
            {
                "ok": True,
                "project_name": "",
                "project": {"details": {"repo_link": repository}},
                "latest_deployment": {"commit": commit_sha},
            },
        )
    state = build_correlation_state(session_id=session_id)
    gh = dict((state.get("graph") or {}).get("github") or {})
    lines: list[str] = []
    if gh:
        lines.append(
            f"GitHub repo **{gh.get('repo') or repository or '—'}** is **{gh.get('status') or 'unknown'}** on commit `{str(gh.get('commit_sha') or commit_sha)[:12] or '—'}`."
        )
    elif repository:
        lines.append("GitHub evidence unavailable — no GitHub API token configured or diagnostics not run yet.")
    else:
        lines.append("GitHub source repo not linked on this Vercel project.")
    return {
        "ok": True,
        "available": bool(gh),
        "lines": lines,
        "evidence": gh,
        "failure_boundary": state["cross_provider_correlation"].get("failure_boundary"),
    }
