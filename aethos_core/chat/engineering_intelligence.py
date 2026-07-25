# SPDX-License-Identifier: Apache-2.0
"""Engineering intelligence lane — deterministic repo/workspace operations."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# --- Intent patterns (high-confidence, substrate-bound) ---

class EngineeringIntent(str, Enum):
    GITHUB_REMOTE_ANALYSIS = "github_remote_analysis"
    WORKSPACE_REGISTER = "workspace_registration"
    WORKSPACE_SCAN = "workspace_scan"
    GIT_STATUS = "git_status"
    GIT_BRANCHES = "git_branches"
    GIT_COMMITS = "git_commits"
    GIT_DIFF = "git_diff_summary"
    ARCHITECTURE = "architecture_analysis"
    DEPENDENCY = "dependency_audit"
    TEST_INTELLIGENCE = "test_analysis"
    WORKFLOW_CI = "workflow_analysis"
    PR_PROPOSAL = "pr_proposal"
    ENGINEERING_PREFLIGHT = "engineering_preflight"


@dataclass(frozen=True)
class ClassifiedIntent:
    intent: EngineeringIntent
    hint: str | None
    path: str | None


_REGISTER_RX = re.compile(
    r"\b(?:register|index)\s+(?:local\s+)?(?:repo|workspace)\b|\bregister\s+local\b",
    re.I,
)
_SCAN_RX = re.compile(
    r"\bscan\s+(?:local\s+)?(?:workspace|repo)\b|\b(?:workspace|repo)\s+scan\b|\bindex\s+repo\b",
    re.I,
)
_GIT_STATUS_RX = re.compile(
    r"\bshow\s+(?:local\s+)?(?:repo\s+)?status\b|\bgit\s+status\b|\blocal\s+repo\s+status\b",
    re.I,
)
_GIT_BRANCHES_RX = re.compile(r"\bshow\s+branches\b|\blist\s+branches\b|\bgit\s+branches\b", re.I)
_GIT_COMMITS_RX = re.compile(
    r"\bshow\s+(?:recent\s+)?commits\b|\blatest\s+commits\b|\bgit\s+log\b|\brecent\s+commits\b",
    re.I,
)
_GIT_DIFF_RX = re.compile(
    r"\bsummari(?:z|s)e\s+(?:uncommitted\s+)?diff\b|\bdiff\s+summary\b|\buncommitted\s+changes\b",
    re.I,
)
_ARCHITECTURE_RX = re.compile(
    r"\banaly(?:z|s)e\s+architecture\b|\barchitecture\s+(?:map|of|for)\b|"
    r"\bshow\s+architecture\b|\bexplain\s+repo\s+structure\b|"
    r"\bscan\s+orchestration\s+layers\b|\barchitecture\s+scan\b",
    re.I,
)
_DEPENDENCY_RX = re.compile(
    r"\b(?:show\s+)?dependency\s+risks?\b|\bdependency\s+(?:audit|scan)\b|"
    r"\bscan\s+packages\b|\bvulnerable\s+dependencies\b|\boutdated\s+(?:packages|dependencies)\b",
    re.I,
)
_TEST_RX = re.compile(
    r"\bshow\s+failing\s+tests\b|\bwhy\s+(?:is\s+)?(?:this\s+)?test\s+failing\b|"
    r"\btest\s+intelligence\b|\bscan\s+(?:for\s+)?failing\s+tests\b",
    re.I,
)
_WORKFLOW_RX = re.compile(
    r"\bscan\s+workflows?\b|\banaly(?:z|s)e\s+ci\b|\bgithub\s+actions\b|\bworkflow\s+(?:analysis|failures)\b",
    re.I,
)
_PR_RX = re.compile(
    r"\bpropose\s+fix\b|\bdraft\s+pr\b|\banaly(?:z|s)e\s+issue\b|\bpr\s+proposal\b",
    re.I,
)
_ENGINEERING_FIX_RX = re.compile(
    r"\bfix\b.*\b(?:github\s+)?workflow\b|\bgoverned\s+patch\b|"
    r"\bprepare\s+and\s+validate\b.*\bmoderni|\bcreate\s+a\s+governed\s+patch\b",
    re.I,
)

_PATH_RX = re.compile(r"(/[\w./~-]+)")
_FOR_HINT_RX = re.compile(r"\b(?:for|of|in)\s+([A-Za-z0-9._/-]+)\b", re.I)
_NAME_HINT_RX = re.compile(
    r"\b(AethOS|aethos|atlas-trader|pilot-os-ui|[A-Za-z][\w-]{2,})\b",
)


def _extract_path(text: str) -> str | None:
    from aethos_core.local_workspace.portfolio import extract_filesystem_paths

    paths = extract_filesystem_paths(text)
    if paths:
        return paths[0]
    m = _PATH_RX.search(text)
    return m.group(1) if m else None


def _extract_hint(text: str) -> str | None:
    m = _FOR_HINT_RX.search(text)
    if m:
        return m.group(1).strip()
    path = _extract_path(text)
    if path:
        return path
    return None


def classify_engineering_intent(text: str) -> ClassifiedIntent | None:
    raw = (text or "").strip()
    if not raw:
        return None

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        workflow_discovery_preemption_blocks_route,
    )

    if workflow_discovery_preemption_blocks_route(raw):
        return None

    from aethos_core.providers.github.operations.repo_remote_read_api import (
        extract_github_repo_hint,
        is_github_remote_repo_analysis_request,
    )

    if is_github_remote_repo_analysis_request(raw):
        return ClassifiedIntent(
            EngineeringIntent.GITHUB_REMOTE_ANALYSIS,
            extract_github_repo_hint(raw),
            None,
        )

    if _REGISTER_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.WORKSPACE_REGISTER, None, _extract_path(raw))

    if _SCAN_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.WORKSPACE_SCAN, _extract_hint(raw), None)

    if _GIT_STATUS_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.GIT_STATUS, _extract_hint(raw), None)

    if _GIT_BRANCHES_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.GIT_BRANCHES, _extract_hint(raw), None)

    if _GIT_COMMITS_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.GIT_COMMITS, _extract_hint(raw), None)

    if _GIT_DIFF_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.GIT_DIFF, _extract_hint(raw), None)

    if _ARCHITECTURE_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.ARCHITECTURE, _extract_hint(raw), None)

    if _DEPENDENCY_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.DEPENDENCY, _extract_hint(raw), None)

    if _TEST_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.TEST_INTELLIGENCE, _extract_hint(raw), None)

    if _WORKFLOW_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.WORKFLOW_CI, _extract_hint(raw), None)

    if _PR_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.PR_PROPOSAL, _extract_hint(raw), None)

    if _ENGINEERING_FIX_RX.search(raw):
        return ClassifiedIntent(EngineeringIntent.ENGINEERING_PREFLIGHT, _extract_hint(raw), None)

    return None


def is_engineering_intelligence_request(text: str) -> bool:
    return classify_engineering_intent(text) is not None


def _routing_meta(
    *,
    intent: EngineeringIntent,
    workspace_name: str | None,
    workspace_id: str | None = None,
    artifact_id: str | None = None,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    meta = {
        "engineering_route_selected": "true",
        "engineering_intent_type": intent.value,
        "workspace_resolved": workspace_name or "canonical",
        "fallback_used": "false",
        "read_only": "true",
        "lane": "engineering_intelligence",
    }
    if workspace_id:
        meta["workspace_id"] = workspace_id
    if artifact_id:
        meta["artifact_id"] = artifact_id
    if extra:
        meta.update(extra)
    return meta


def execute_engineering_intent(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    classified = classify_engineering_intent(text)
    if classified is None:
        return None

    from aethos_core.local_workspace.session_context import resolve_operational_hint, set_active_workspace

    hint = resolve_operational_hint(classified.hint, session_id=session_id)
    intent = classified.intent

    if intent == EngineeringIntent.GITHUB_REMOTE_ANALYSIS:
        return _handle_github_remote_analysis(text, hint=classified.hint, session_id=session_id)

    if intent == EngineeringIntent.WORKSPACE_REGISTER:
        return _handle_register(classified.path, session_id=session_id)

    if intent == EngineeringIntent.WORKSPACE_SCAN:
        return _handle_scan(hint, session_id=session_id)

    if intent == EngineeringIntent.GIT_STATUS:
        return _handle_git_status(hint, session_id=session_id)

    if intent == EngineeringIntent.GIT_BRANCHES:
        return _handle_git_branches(hint, session_id=session_id)

    if intent == EngineeringIntent.GIT_COMMITS:
        return _handle_git_commits(hint, session_id=session_id)

    if intent == EngineeringIntent.GIT_DIFF:
        return _handle_git_diff(hint, session_id=session_id)

    if intent == EngineeringIntent.ARCHITECTURE:
        return _handle_architecture(hint, session_id=session_id, text=text)

    if intent == EngineeringIntent.DEPENDENCY:
        return _handle_dependency(hint, session_id=session_id, text=text)

    if intent == EngineeringIntent.TEST_INTELLIGENCE:
        return _handle_tests(hint, session_id=session_id)

    if intent == EngineeringIntent.WORKFLOW_CI:
        return _handle_workflows(hint, session_id=session_id, text=text)

    if intent == EngineeringIntent.PR_PROPOSAL:
        return _handle_pr_proposal(hint, text=text, session_id=session_id)

    if intent == EngineeringIntent.ENGINEERING_PREFLIGHT:
        return _handle_engineering_preflight(hint, text=text, session_id=session_id)

    return None


def engineering_intelligence_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    """Alias for handler integration."""
    return execute_engineering_intent(text, session_id=session_id)


def _github_remote_engineering_fallback(
    text: str,
    *,
    hint: str | None,
    intent: EngineeringIntent,
    reply_intent: str,
) -> tuple[str, str, dict[str, str]] | None:
    """Hosted engineering review via GitHub API when no local workspace is registered."""
    from aethos_core.providers.github.operations.repo_remote_read_api import (
        analyze_github_repo_for_chat,
        extract_github_repo_hint,
        is_github_remote_repo_analysis_request,
    )
    from aethos_core.remote_workspace.github_clone import parse_github_repository

    repo_hint = (hint or "").strip() or extract_github_repo_hint(text) or ""
    explicit_remote = (
        is_github_remote_repo_analysis_request(text)
        or bool(parse_github_repository(text))
        or (repo_hint and "/" in repo_hint)
    )
    if not explicit_remote:
        from aethos_core.local_workspace.registry import find_workspace_by_hint

        if find_workspace_by_hint(hint):
            return None

    if not repo_hint:
        return None

    result = analyze_github_repo_for_chat(text, repository=repo_hint)
    snapshot = result.get("snapshot") or {}
    repository = str(snapshot.get("repository") or repo_hint or "unknown")
    return (
        str(result.get("report") or "Remote engineering review unavailable."),
        reply_intent,
        _routing_meta(
            intent=intent,
            workspace_name=repository,
            extra={
                "github_remote_read": "true",
                "repository": repository,
                "engineering_review": "true",
                "fallback_used": "true",
            },
        ),
    )


def _handle_github_remote_analysis(
    text: str,
    *,
    hint: str | None,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    from aethos_core.providers.github.operations.repo_remote_read_api import (
        analyze_github_repo_for_chat,
        extract_github_repo_hint,
    )

    repo_hint = (hint or "").strip() or extract_github_repo_hint(text) or ""
    result = analyze_github_repo_for_chat(text, repository=repo_hint)
    snapshot = result.get("snapshot") or {}
    repository = str(snapshot.get("repository") or repo_hint or "unknown")
    return (
        str(result.get("report") or "GitHub repo analysis unavailable."),
        "github_remote_analysis",
        _routing_meta(
            intent=EngineeringIntent.GITHUB_REMOTE_ANALYSIS,
            workspace_name=repository,
            extra={
                "github_remote_read": "true",
                "repository": repository,
                "read_only": "true",
            },
        ),
    )


def _handle_register(path: str | None, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.local_workspace.memory.engineering_memory import hydrate_workspace_memory
    from aethos_core.local_workspace.registry import register_workspace
    from aethos_core.local_workspace.readonly.actions import run_workspace_scan

    if not path:
        return (
            "Register a workspace with an absolute path, e.g. "
            "`register local repo ~/projects/aethos`.",
            "workspace_register_help",
            _routing_meta(intent=EngineeringIntent.WORKSPACE_REGISTER, workspace_name=None),
        )
    try:
        from aethos_core.local_workspace.session_context import set_active_workspace

        record = register_workspace(path=path)
        scan = run_workspace_scan(Path(record["path"]), workspace_id=record["workspace_id"])
        hydrate_workspace_memory(record, scan.get("scan") or {})
        set_active_workspace(session_id, record)
    except ValueError as exc:
        return (
            str(exc),
            "workspace_register_failed",
            _routing_meta(intent=EngineeringIntent.WORKSPACE_REGISTER, workspace_name=None),
        )

    arch = scan.get("scan", {}).get("architecture", {})
    artifact_id = str((scan.get("artifact") or {}).get("artifact_id") or "")
    body = "\n".join(
        [
            "# Workspace registered (readonly)",
            "",
            f"**Name:** {record.get('name')}",
            f"**Path:** `{record.get('path')}`",
            f"**Branch:** {scan.get('scan', {}).get('git_status', {}).get('branch') or '—'}",
            f"**Stack:** {', '.join(record.get('stack', {}).get('badges') or [])}",
            f"**Artifact:** `{artifact_id}`" if artifact_id else "",
            "",
            arch.get("summary") or "Workspace registered and scanned.",
            "",
            "Mission Control → Engineering → Local Workspaces will show this workspace.",
        ]
    )
    return (
        body,
        "workspace_registered",
        _routing_meta(
            intent=EngineeringIntent.WORKSPACE_REGISTER,
            workspace_name=str(record.get("name")),
            workspace_id=str(record.get("workspace_id")),
            artifact_id=artifact_id or None,
        ),
    )


def _handle_scan(hint: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.local_workspace.memory.engineering_memory import hydrate_workspace_memory
    from aethos_core.local_workspace.registry import find_workspace_by_hint
    from aethos_core.local_workspace.readonly.actions import run_workspace_scan
    from aethos_core.local_workspace.registry import resolve_workspace_path

    repo = resolve_workspace_path(hint)
    ws = find_workspace_by_hint(hint)
    scan = run_workspace_scan(repo, workspace_id=ws.get("workspace_id") if ws else None)
    if ws:
        hydrate_workspace_memory(ws, scan.get("scan") or {})
    arch = scan.get("scan", {}).get("architecture", {})
    artifact_id = str((scan.get("artifact") or {}).get("artifact_id") or "")
    return (
        arch.get("summary") or "Workspace scan complete.",
        "local_repo_scan",
        _routing_meta(
            intent=EngineeringIntent.WORKSPACE_SCAN,
            workspace_name=ws.get("name") if ws else repo.name,
            workspace_id=str(ws.get("workspace_id")) if ws else None,
            artifact_id=artifact_id or None,
        ),
    )


def _handle_git_status(hint: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.local_workspace.readonly.actions import run_git_status_report
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    result = run_git_status_report(hint=hint, session_id=session_id)
    ws = find_workspace_by_hint(hint)
    artifact_id = str((result.get("artifact") or {}).get("artifact_id") or "")
    return (
        result.get("report") or "Git status unavailable.",
        "git_status_snapshot",
        _routing_meta(
            intent=EngineeringIntent.GIT_STATUS,
            workspace_name=ws.get("name") if ws else hint,
            workspace_id=str(ws.get("workspace_id")) if ws else None,
            artifact_id=artifact_id or None,
        ),
    )


def _handle_git_branches(hint: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.local_workspace.git.intelligence import git_branches
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    repo = _repo_from_hint(hint, session_id=session_id)
    branches = git_branches(repo)
    ws = find_workspace_by_hint(hint)
    lines = ["# Git branches (readonly)", "", f"**Repo:** `{repo}`", ""]
    for b in branches.get("branches") or []:
        lines.append(f"- {b}")
    return (
        "\n".join(lines),
        "git_branches",
        _routing_meta(intent=EngineeringIntent.GIT_BRANCHES, workspace_name=ws.get("name") if ws else hint),
    )


def _handle_git_commits(hint: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.local_workspace.git.intelligence import git_recent_commits
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    repo = _repo_from_hint(hint, session_id=session_id)
    commits = git_recent_commits(repo)
    ws = find_workspace_by_hint(hint)
    lines = ["# Recent commits (readonly)", "", f"**Repo:** `{repo}`", ""]
    for c in commits.get("commits") or []:
        lines.append(f"- {c}")
    return (
        "\n".join(lines),
        "git_commits",
        _routing_meta(intent=EngineeringIntent.GIT_COMMITS, workspace_name=ws.get("name") if ws else hint),
    )


def _handle_git_diff(hint: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.local_workspace.git.intelligence import git_diff_summary, git_status_snapshot
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    repo = _repo_from_hint(hint, session_id=session_id)
    diff = git_diff_summary(repo)
    git = git_status_snapshot(repo)
    ws = find_workspace_by_hint(hint)
    body = "\n".join(
        [
            "# Diff summary (readonly)",
            "",
            f"**Repo:** `{repo}`",
            f"**Branch:** {git.get('branch') or 'unknown'}",
            f"**Modified:** {git.get('modified_count', 0)} · **Untracked:** {git.get('untracked_count', 0)}",
            "",
            "```",
            diff.get("shortstat") or diff.get("diff_stat") or "(no diff)",
            "```",
        ]
    )
    return (
        body,
        "git_diff_summary",
        _routing_meta(intent=EngineeringIntent.GIT_DIFF, workspace_name=ws.get("name") if ws else hint),
    )


def _handle_architecture(hint: str, *, session_id: str, text: str = "") -> tuple[str, str, dict[str, str]]:
    remote = _github_remote_engineering_fallback(
        text,
        hint=hint,
        intent=EngineeringIntent.ARCHITECTURE,
        reply_intent="architecture_analysis",
    )
    if remote is not None:
        return remote

    from aethos_core.local_workspace.memory.engineering_memory import hydrate_workspace_memory
    from aethos_core.local_workspace.readonly.actions import run_architecture_report
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    result = run_architecture_report(hint=hint, session_id=session_id)
    ws = find_workspace_by_hint(hint)
    if ws:
        hydrate_workspace_memory(ws, {"architecture": result.get("analysis")})
    artifact_id = str((result.get("artifact") or {}).get("artifact_id") or "")
    return (
        result.get("report") or "Architecture analysis unavailable.",
        "architecture_analysis",
        _routing_meta(
            intent=EngineeringIntent.ARCHITECTURE,
            workspace_name=ws.get("name") if ws else hint,
            workspace_id=str(ws.get("workspace_id")) if ws else None,
            artifact_id=artifact_id or None,
        ),
    )


def _handle_dependency(hint: str, *, session_id: str, text: str = "") -> tuple[str, str, dict[str, str]]:
    remote = _github_remote_engineering_fallback(
        text,
        hint=hint,
        intent=EngineeringIntent.DEPENDENCY,
        reply_intent="dependency_audit",
    )
    if remote is not None:
        return remote

    from aethos_core.local_workspace.readonly.actions import run_dependency_report
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    result = run_dependency_report(hint=hint, session_id=session_id)
    ws = find_workspace_by_hint(hint)
    artifact_id = str((result.get("artifact") or {}).get("artifact_id") or "")
    return (
        result.get("report") or "Dependency audit unavailable.",
        "dependency_audit",
        _routing_meta(
            intent=EngineeringIntent.DEPENDENCY,
            workspace_name=ws.get("name") if ws else hint,
            workspace_id=str(ws.get("workspace_id")) if ws else None,
            artifact_id=artifact_id or None,
        ),
    )


def _handle_tests(hint: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.local_workspace.readonly.actions import run_test_report
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    result = run_test_report(hint=hint, session_id=session_id)
    ws = find_workspace_by_hint(hint)
    artifact_id = str((result.get("artifact") or {}).get("artifact_id") or "")
    return (
        result.get("report") or "Test analysis unavailable.",
        "test_failure_report",
        _routing_meta(
            intent=EngineeringIntent.TEST_INTELLIGENCE,
            workspace_name=ws.get("name") if ws else hint,
            workspace_id=str(ws.get("workspace_id")) if ws else None,
            artifact_id=artifact_id or None,
        ),
    )


def _handle_workflows(hint: str, *, session_id: str, text: str = "") -> tuple[str, str, dict[str, str]]:
    remote = _github_remote_engineering_fallback(
        text,
        hint=hint,
        intent=EngineeringIntent.WORKFLOW_CI,
        reply_intent="workflow_analysis",
    )
    if remote is not None:
        return remote

    from aethos_core.local_workspace.readonly.actions import run_workflow_report
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    result = run_workflow_report(hint=hint, session_id=session_id)
    ws = find_workspace_by_hint(hint)
    artifact_id = str((result.get("artifact") or {}).get("artifact_id") or "")
    return (
        result.get("report") or "Workflow analysis unavailable.",
        "workflow_analysis",
        _routing_meta(
            intent=EngineeringIntent.WORKFLOW_CI,
            workspace_name=ws.get("name") if ws else hint,
            workspace_id=str(ws.get("workspace_id")) if ws else None,
            artifact_id=artifact_id or None,
        ),
    )


def _handle_engineering_preflight(hint: str, *, text: str, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.engineering.governance.engineering_preflight import run_and_record_engineering_preflight
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    repo = _repo_from_hint(hint, session_id=session_id)
    ws = find_workspace_by_hint(hint)
    preflight = run_and_record_engineering_preflight(
        user_request=text,
        repo=repo,
        workspace_hint=hint,
        session_id=session_id,
        source="chat",
    )
    meta = _routing_meta(
        intent=EngineeringIntent.ENGINEERING_PREFLIGHT,
        workspace_name=ws.get("name") if ws else hint,
        workspace_id=str(ws.get("workspace_id")) if ws else None,
        extra={
            "read_only": "false",
            "engineering_preflight_id": preflight.get("preflight_id") or "",
            "approval_status": "pending",
            "execution_enabled": "false",
        },
    )
    return preflight.get("report") or "Engineering preflight complete.", "engineering_preflight", meta


def _handle_pr_proposal(hint: str, *, text: str, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.local_workspace.mutations.foundation import build_pr_proposal_stub
    from aethos_core.local_workspace.registry import find_workspace_by_hint

    ws = find_workspace_by_hint(hint)
    proposal = build_pr_proposal_stub(provider="github", target=hint, user_request=text)
    body = "\n".join(
        [
            "# PR proposal (preflight-only — no auto-merge)",
            "",
            f"**Target workspace:** {ws.get('name') if ws else hint}",
            f"**Status:** {proposal.get('status')}",
            "",
            "## Verification plan",
            *[f"- {step}" for step in proposal.get("verification_plan") or []],
            "",
            "## Required lifecycle",
            " → ".join(proposal.get("required_lifecycle") or []),
            "",
            "**Blocked:** unrestricted shell · auto-merge · force push · silent coding",
        ]
    )
    return (
        body,
        "pr_proposal",
        _routing_meta(
            intent=EngineeringIntent.PR_PROPOSAL,
            workspace_name=ws.get("name") if ws else hint,
            workspace_id=str(ws.get("workspace_id")) if ws else None,
        ),
    )


def build_engineering_context(*, session_id: str = "default") -> dict[str, Any]:
    """Operational context for chat panel + MC hydration."""
    from aethos_core.local_workspace.git.intelligence import git_status_snapshot
    from aethos_core.local_workspace.memory.engineering_memory import get_engineering_memory
    from aethos_core.local_workspace.registry import find_workspace_by_hint, list_workspaces
    from aethos_core.local_workspace.session_context import get_active_workspace
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint

    active = get_active_workspace(session_id)
    hint = active.get("name") if active else None
    if not hint:
        rows = list_workspaces()
        if len(rows) == 1:
            active = rows[0]
            hint = active.get("name")

    memory = get_engineering_memory()
    repo_path = None
    git = {}
    architecture_summary = None
    dependency_severity = None
    if hint:
        ws = find_workspace_by_hint(str(hint))
        if ws:
            active = ws
            repo_path = ws.get("path")
            mem_repo = (memory.get("repos") or {}).get(str(repo_path), {})
            architecture_summary = mem_repo.get("architecture_summary")
            dependency_severity = mem_repo.get("dependency_severity")
        try:
            repo = _repo_from_hint(str(hint), session_id=session_id)
            git = git_status_snapshot(repo)
            repo_path = str(repo)
        except Exception:
            pass

    return {
        "ok": True,
        "session_id": session_id,
        "active_workspace": active,
        "git": git,
        "architecture_summary": architecture_summary,
        "dependency_severity": dependency_severity,
        "engineering_memory_events": (memory.get("events") or [])[:5],
        "workspaces_count": len(list_workspaces()),
    }
