# SPDX-License-Identifier: Apache-2.0
"""Phase 1 — local workspace deployment source discovery."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from aethos_core.local_workspace.git.intelligence import git_status_snapshot
from aethos_core.local_workspace.canonical_path import evaluate_workspace_path
from aethos_core.local_workspace.registry import find_workspace_by_hint, list_workspaces
from aethos_core.runtime.workspace_diagnostics import resolve_configured_workspace_root
from aethos_core.local_workspace.scanner import read_package_scripts, scan_workspace_stack
from aethos_core.security.secret_redaction import redact_text


def discover_local_workspace_deployment_source(*, hint: str = "aethos", user_text: str = "") -> dict[str, Any]:
    """Inspect local workspace registry and filesystem — never raises."""
    from aethos_core.local_workspace.portfolio import find_project_in_portfolio, resolve_repo_reference

    registry_rows = list_workspaces()
    if user_text or hint:
        resolved = resolve_repo_reference(user_text or hint)
        resolved_path = str(resolved.get("resolved_path") or resolved.get("path") or "").strip()
        source = str(resolved.get("source") or "")
        if resolved_path and source in {
            "portfolio_path",
            "portfolio_name",
            "portfolio_name_partial",
            "portfolio_remote",
            "portfolio_child_path",
            "chat_path",
            "registered",
        }:
            portfolio_hint = str(resolved.get("name") or hint or Path(resolved_path).name)
            workspace_row = find_workspace_by_hint(portfolio_hint) or resolved
            return _build_source_from_root(
                Path(resolved_path),
                workspace_row=workspace_row if isinstance(workspace_row, dict) else None,
                registry_count=len(registry_rows),
                resolution_source=source,
            )

        portfolio_row = find_project_in_portfolio(hint, text=user_text)
        if portfolio_row and portfolio_row.get("path"):
            return _build_source_from_root(
                Path(str(portfolio_row["path"])),
                workspace_row=portfolio_row,
                registry_count=len(registry_rows),
                resolution_source=str(portfolio_row.get("source") or "portfolio"),
            )

    workspace_row = find_workspace_by_hint(hint)
    try:
        if (hint or "").strip().lower() in ("aethos", "this", "thisrepo"):
            raw = resolve_configured_workspace_root()
        else:
            from aethos_core.local_workspace.registry import resolve_workspace_path

            raw = resolve_workspace_path(hint)
    except Exception as exc:
        return _blocked(
            "LOCAL_WORKSPACE_NOT_CONFIGURED",
            f"Could not resolve workspace path: {redact_text(str(exc))}",
            registry_count=len(registry_rows),
        )

    evaluation = evaluate_workspace_path(raw)
    if not evaluation.ok:
        code = evaluation.blocker_code or "LOCAL_WORKSPACE_NOT_CONFIGURED"
        return _blocked(
            code,
            evaluation.detail or "Local workspace path is not usable for deployment.",
            workspace_root=str(evaluation.path),
            registry_count=len(registry_rows),
            safe_next_command=evaluation.safe_next_command
            or "Open Mission Control → Code workspaces and register the AethOS repo path.",
            canonicalized="true" if evaluation.canonicalized else "false",
            original_workspace_root=str(evaluation.original_path),
        )

    root = evaluation.path

    return _build_source_from_root(
        root,
        workspace_row=workspace_row,
        registry_count=len(registry_rows),
        evaluation=evaluation,
    )


def _build_source_from_root(
    root: Path,
    *,
    workspace_row: dict[str, Any] | None,
    registry_count: int,
    resolution_source: str = "",
    evaluation: Any | None = None,
) -> dict[str, Any]:
    if not root.is_dir():
        return _blocked(
            "LOCAL_WORKSPACE_NOT_CONFIGURED",
            "No local workspace directory is configured.",
            registry_count=registry_count,
        )

    has_project_markers = any(
        (root / marker).exists()
        for marker in (".git", "pyproject.toml", "package.json", "web/package.json")
    )
    if not has_project_markers:
        return _blocked(
            "LOCAL_WORKSPACE_NOT_CONFIGURED",
            f"Path `{root.name}` does not look like a deployable workspace.",
            workspace_root=str(root),
            registry_count=registry_count,
        )

    try:
        stack = scan_workspace_stack(root)
    except OSError as exc:
        return _blocked(
            "LOCAL_WORKSPACE_NOT_CONFIGURED",
            f"Could not scan workspace: {redact_text(str(exc))}",
            workspace_root=str(root),
            registry_count=registry_count,
        )
    try:
        git_status = git_status_snapshot(root) if stack.get("has_git") else {"ok": False, "branch": None}
    except OSError as exc:
        git_status = {"ok": False, "branch": None, "detail": redact_text(str(exc))}
    try:
        scripts = read_package_scripts(root)
    except OSError as exc:
        scripts = {"scripts": {}, "path": None, "detail": redact_text(str(exc))}
    start_candidates = _start_command_candidates(scripts.get("scripts") or {})
    remotes = _git_remotes(root)
    eval_obj = evaluation

    return {
        "ok": True,
        "blocker_code": "",
        "workspace_root": str(root),
        "workspace_id": str((workspace_row or {}).get("workspace_id") or ""),
        "workspace_name": str((workspace_row or {}).get("name") or root.name),
        "repo_name": root.name,
        "registered_in_catalog": bool((workspace_row or {}).get("workspace_id")),
        "registry_count": registry_count,
        "resolution_source": resolution_source,
        "canonicalized": bool(getattr(eval_obj, "canonicalized", False)),
        "original_workspace_root": str(getattr(eval_obj, "original_path", "")) if getattr(eval_obj, "canonicalized", False) else "",
        "stack": stack,
        "git_status": git_status,
        "branch": git_status.get("branch"),
        "git_clean": git_status.get("modified_count", 0) == 0 and git_status.get("untracked_count", 0) == 0,
        "remotes_preview": remotes,
        "build_files": _build_files_present(root),
        "start_command_candidates": start_candidates,
        "package_scripts_path": scripts.get("path"),
    }


def format_local_workspace_deployment_source_report(source: dict[str, Any]) -> str:
    if not source.get("ok"):
        code = source.get("blocker_code") or "LOCAL_WORKSPACE_NOT_CONFIGURED"
        lines = [
            f"**Local workspace not configured** (`{code}`)",
            "",
            f"- Detail: {source.get('detail') or 'unknown'}",
            f"- Registry entries: **{source.get('registry_count', 0)}**",
        ]
        if source.get("original_workspace_root"):
            lines.append(f"- Registered path: `{source.get('original_workspace_root')}`")
        if code == "LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH":
            lines.append(
                "- This path looks like a generated mutation workspace, not the real repo root."
            )
        lines.extend(
            [
                "",
                f"**Required action:** {source.get('safe_next_command') or 'Register the workspace in Local Workspaces.'}",
                "",
                "No mutation has been performed.",
            ]
        )
        return "\n".join(lines)
    stack = source.get("stack") or {}
    lines = [
        "**Local workspace deployment source**",
        "",
        f"- Workspace: `{source.get('workspace_name')}`",
        f"- Root: `{source.get('workspace_root')}`",
        f"- Registered in catalog: **{'yes' if source.get('registered_in_catalog') else 'no'}**",
        f"- Stack: {', '.join(stack.get('badges') or []) or 'unknown'}",
        f"- Branch: `{source.get('branch') or 'unknown'}`",
        f"- Git modified/untracked: **{((source.get('git_status') or {}).get('modified_count', 0))}** / "
        f"**{((source.get('git_status') or {}).get('untracked_count', 0))}**",
        f"- Build files: {', '.join(source.get('build_files') or []) or 'none detected'}",
    ]
    if source.get("resolution_source"):
        lines.append(f"- Resolution: `{source.get('resolution_source')}`")
    starts = list(source.get("start_command_candidates") or [])
    if starts:
        lines.append(f"- Start command candidates: `{starts[0]}`" + (f" (+{len(starts)-1} more)" if len(starts) > 1 else ""))
    return "\n".join(lines)


def _blocked(code: str, detail: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "blocker_code": code,
        "detail": detail,
        "safe_next_command": extra.pop(
            "safe_next_command",
            "Open Mission Control → Code workspaces and register the AethOS repo path.",
        ),
        **extra,
    }


def _git_remotes(repo: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "remote", "-v"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if proc.returncode != 0:
            return []
        return [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()][:4]
    except (OSError, subprocess.TimeoutExpired):
        return []


def _build_files_present(repo: Path) -> list[str]:
    names = []
    for rel in (
        "Dockerfile",
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "web/package.json",
        "railway.json",
        "Procfile",
        ".env.example",
    ):
        if (repo / rel).is_file():
            names.append(rel)
    return names


def _start_command_candidates(scripts: dict[str, str]) -> list[str]:
    out: list[str] = []
    for key in ("start", "dev", "serve", "start:prod"):
        val = str(scripts.get(key) or "").strip()
        if val:
            out.append(f"npm run {key}" if not val.startswith("npm") else val)
    return out[:4]
