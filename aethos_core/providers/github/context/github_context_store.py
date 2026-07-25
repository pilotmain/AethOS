# SPDX-License-Identifier: Apache-2.0
"""Session-scoped GitHub operational context for diagnostics → rerun continuity."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

_INVALID_REPOS = frozenset({"owner/aethos", "owner/repo", "unknown/aethos"})
_PLACEHOLDER_OWNERS = frozenset({"owner", "unknown"})

_STORE: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def assert_valid_repo_context(repo_full_name: str) -> tuple[bool, str | None]:
    slug = (repo_full_name or "").strip()
    if not slug:
        return False, "GitHub repository context is missing."
    lower = slug.lower()
    if lower in _INVALID_REPOS:
        return False, f"Repository `{slug}` is a placeholder, not a real GitHub repo."
    if "/" not in slug:
        return False, f"Repository `{slug}` is not a valid owner/repo slug."
    owner, repo = slug.split("/", 1)
    if not owner or not repo:
        return False, "GitHub repository context is missing owner or repo name."
    if owner.lower() in _PLACEHOLDER_OWNERS:
        return False, f"Repository owner `{owner}` is not a resolved GitHub account."
    if owner.lower() in _PLACEHOLDER_OWNERS and repo.lower() in {"repo", "aethos"}:
        return False, f"Repository `{slug}` is a placeholder, not a real GitHub repo."
    return True, None


def save_github_context_from_evidence(session_id: str, evidence: dict[str, Any]) -> dict[str, Any] | None:
    repo_data = dict(evidence.get("repo") or {})
    repo_full = str(evidence.get("repository") or repo_data.get("full_name") or repo_data.get("repository") or "")
    valid, _ = assert_valid_repo_context(repo_full)
    if not valid:
        return None

    branch_data = dict(evidence.get("branch") or {})
    workflow_diag = dict(evidence.get("workflow_diagnostic") or {})
    workflow_runs = list((evidence.get("workflow_runs") or {}).get("runs") or [])
    checks = dict(evidence.get("checks") or {})
    commits = list((evidence.get("commits") or {}).get("commits") or [])

    failed_workflow_runs = [
        run
        for run in workflow_runs
        if isinstance(run, dict) and str(run.get("conclusion") or "").lower() == "failure"
    ]
    head_sha = str(commits[0].get("sha") or "") if commits else str(branch_data.get("sha") or "")
    default_branch = str(repo_data.get("default_branch") or branch_data.get("branch") or "main")
    active_branch = str(branch_data.get("branch") or default_branch)
    owner, repo = repo_full.split("/", 1)

    from aethos_core.cross_provider_correlation.correlation_store import get_session_snapshot

    snapshot = get_session_snapshot(session_id)
    context = {
        "repo_full_name": repo_full,
        "owner": owner,
        "repo": repo,
        "default_branch": default_branch,
        "active_branch": active_branch,
        "head_sha": head_sha,
        "latest_workflow_runs": workflow_runs[:10],
        "failed_workflow_runs": failed_workflow_runs[:10],
        "failed_checks": list(checks.get("checks") or []),
        "last_diagnosed_at": _now_iso(),
        "correlation_snapshot_id": str(snapshot.get("updated_at") or _now_iso()),
        "latest_failed_run": dict(workflow_diag.get("latest_failed_run") or {}),
    }
    bucket = _session_bucket(session_id)
    bucket["active"] = context
    return context


def get_active_github_context(session_id: str = "default") -> dict[str, Any] | None:
    ctx = (_session_bucket(session_id).get("active") or {})
    if not isinstance(ctx, dict) or not ctx:
        return None
    valid, _ = assert_valid_repo_context(str(ctx.get("repo_full_name") or ""))
    return ctx if valid else None


def save_github_rerun_context(session_id: str, rerun: dict[str, Any]) -> dict[str, Any]:
    entry = dict(rerun)
    repo = str(entry.get("rerun_target_repo") or entry.get("repository") or "")
    valid, _ = assert_valid_repo_context(repo)
    if not valid:
        entry.pop("rerun_target_repo", None)
        entry.pop("repository", None)
    else:
        entry["rerun_target_repo"] = repo
    entry["updated_at"] = _now_iso()
    _session_bucket(session_id)["rerun"] = entry
    return entry


def get_github_rerun_context(session_id: str = "default") -> dict[str, Any] | None:
    ctx = (_session_bucket(session_id).get("rerun") or {})
    if not isinstance(ctx, dict) or not ctx:
        return None
    repo = str(ctx.get("rerun_target_repo") or ctx.get("repository") or "")
    if repo:
        valid, _ = assert_valid_repo_context(repo)
        if not valid:
            return None
    return ctx


def resolve_rerun_repository(
    *,
    session_id: str = "default",
    user_request: str = "",
    target_hints: list[str] | None = None,
    repository: str = "",
) -> dict[str, Any]:
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import extract_github_repo_slug

    explicit = extract_github_repo_slug(user_request)
    if not explicit and target_hints:
        for hint in target_hints:
            hint_text = str(hint or "").strip()
            if "/" in hint_text:
                explicit = hint_text
                break
    if explicit:
        valid, err = assert_valid_repo_context(explicit)
        if valid:
            return {"repo": explicit, "source": "explicit"}
        return {"repo": None, "source": "invalid", "error": err}

    if repository:
        valid, err = assert_valid_repo_context(repository)
        if valid:
            return {"repo": repository, "source": "parameter"}
        return {"repo": None, "source": "invalid", "error": err}

    active = get_active_github_context(session_id)
    if active:
        repo = str(active.get("repo_full_name") or "")
        return {"repo": repo, "source": "github_context", "context": active}

    from aethos_core.cross_provider_correlation.correlation_store import get_session_snapshot

    snapshot = get_session_snapshot(session_id)
    gh = dict(snapshot.get("github") or {})
    repo = str(gh.get("repo") or "")
    valid, err = assert_valid_repo_context(repo)
    if valid:
        return {"repo": repo, "source": "correlation_store"}

    return {
        "repo": None,
        "source": "missing",
        "error": err or "No active GitHub repository context. Diagnose a repo first or specify owner/repo.",
    }


def compose_no_failed_workflow_guidance(*, repository: str) -> list[str]:
    return [
        f"I inspected **{repository}**, but no failed workflow run is available to rerun.",
        "",
        "No mutation has been performed.",
        "No approval is required.",
        "",
        "Available next steps:",
        "- inspect recent workflow runs",
        "- show failed checks",
        "- diagnose another repo",
    ]


def _session_bucket(session_id: str) -> dict[str, Any]:
    key = (session_id or "default").strip() or "default"
    return _STORE.setdefault(key, {})


def clear_github_context_for_tests() -> None:
    _STORE.clear()
