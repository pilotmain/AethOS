# SPDX-License-Identifier: Apache-2.0
"""Canonical local workspace roots — reject mutation artifact sandboxes."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

MUTATION_WORKSPACES_SEGMENT = "data/agent_artifacts/mutation_workspaces"
ARTIFACT_PATH_WARNING = (
    "This looks like a generated mutation workspace, not a project root. "
    "Use the real repo root instead."
)

SCAN_IGNORE_DIR_NAMES = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "mutation_workspaces",
    }
)

_MUTATION_REPO_RX = re.compile(
    r"mutation_workspaces/(mws-[a-f0-9]+)/repo",
    re.I,
)


@dataclass(frozen=True)
class WorkspacePathEvaluation:
    original_path: Path
    path: Path
    ok: bool
    blocker_code: str = ""
    detail: str = ""
    canonicalized: bool = False
    safe_next_command: str = ""


def normalize_path_str(path: Path | str) -> str:
    return str(path).replace("\\", "/").rstrip("/")


def is_mutation_artifact_path(path: Path | str) -> bool:
    return MUTATION_WORKSPACES_SEGMENT in normalize_path_str(path)


def is_recursive_mutation_artifact_path(path: Path | str) -> bool:
    normalized = normalize_path_str(path)
    return normalized.count(f"{MUTATION_WORKSPACES_SEGMENT}/") >= 2


def validate_registration_path(path: Path) -> None:
    """Raise ValueError when a user tries to register an artifact sandbox path."""
    if is_mutation_artifact_path(path):
        raise ValueError(ARTIFACT_PATH_WARNING)


def path_should_be_skipped_for_scan(path: Path) -> bool:
    parts = path.parts
    if any(part in SCAN_IGNORE_DIR_NAMES for part in parts):
        return True
    normalized = normalize_path_str(path)
    if "data/agent_artifacts" in normalized:
        return True
    return False


def iter_repo_files_limited(
    repo: Path,
    *,
    max_depth: int = 6,
    suffixes: tuple[str, ...] = (".py", ".ts", ".tsx", ".yaml", ".yml"),
) -> Iterator[Path]:
    """Bounded file walk that skips generated artifact directories."""
    repo = repo.resolve()
    root_depth = len(repo.parts)
    stack = [repo]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for child in children:
            if child.is_dir():
                if path_should_be_skipped_for_scan(child):
                    continue
                if len(child.parts) - root_depth <= max_depth:
                    stack.append(child)
                continue
            if path_should_be_skipped_for_scan(child):
                continue
            if len(child.parts) - root_depth > max_depth:
                continue
            if suffixes and child.suffix not in suffixes:
                continue
            yield child


def evaluate_workspace_path(path: Path, *, require_git_remote: bool = False) -> WorkspacePathEvaluation:
    """Validate and canonicalize a workspace path — never raises."""
    try:
        original = path.expanduser()
        if not original.is_dir():
            return WorkspacePathEvaluation(
                original_path=original,
                path=original,
                ok=False,
                blocker_code="LOCAL_WORKSPACE_NOT_CONFIGURED",
                detail="Workspace path is not a directory.",
                safe_next_command="Open Mission Control → Code workspaces and register the AethOS repo path.",
            )

        try:
            resolved = original.resolve()
        except OSError as exc:
            return WorkspacePathEvaluation(
                original_path=original,
                path=original,
                ok=False,
                blocker_code="LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH",
                detail=f"Could not resolve workspace path safely: {exc}",
                safe_next_command=ARTIFACT_PATH_WARNING,
            )

        if is_recursive_mutation_artifact_path(resolved):
            suggested = infer_canonical_repo_root(resolved, require_git_remote=require_git_remote)
            detail = (
                "Registered path points at a nested mutation artifact workspace, not the real repo root."
            )
            if suggested is not None:
                detail += f" Use `{suggested}` instead."
            return WorkspacePathEvaluation(
                original_path=original,
                path=resolved,
                ok=False,
                blocker_code="LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH",
                detail=detail,
                safe_next_command=ARTIFACT_PATH_WARNING,
            )

        if is_mutation_artifact_path(resolved):
            canonical = infer_canonical_repo_root(resolved, require_git_remote=require_git_remote)
            if canonical is not None and canonical != resolved:
                return WorkspacePathEvaluation(
                    original_path=original,
                    path=canonical,
                    ok=True,
                    canonicalized=True,
                )
            return WorkspacePathEvaluation(
                original_path=original,
                path=resolved,
                ok=False,
                blocker_code="LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH",
                detail=ARTIFACT_PATH_WARNING,
                safe_next_command=ARTIFACT_PATH_WARNING,
            )

        if not is_valid_canonical_repo_root(resolved, require_git_remote=require_git_remote):
            return WorkspacePathEvaluation(
                original_path=original,
                path=resolved,
                ok=False,
                blocker_code="LOCAL_WORKSPACE_NOT_CONFIGURED",
                detail=f"Path `{resolved.name}` does not look like a deployable repo root.",
                safe_next_command="Open Mission Control → Code workspaces and register the AethOS repo path.",
            )

        return WorkspacePathEvaluation(
            original_path=original,
            path=resolved,
            ok=True,
        )
    except OSError as exc:
        return WorkspacePathEvaluation(
            original_path=path,
            path=path,
            ok=False,
            blocker_code="LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH",
            detail=str(exc),
            safe_next_command=ARTIFACT_PATH_WARNING,
        )


def canonicalize_workspace_path(path: Path, *, require_git_remote: bool = False) -> Path:
    """Return the best canonical repo root for scanning and git operations."""
    evaluation = evaluate_workspace_path(path, require_git_remote=require_git_remote)
    if evaluation.ok:
        return evaluation.path
    if evaluation.blocker_code == "LOCAL_WORKSPACE_RECURSIVE_ARTIFACT_PATH":
        try:
            return path.expanduser().resolve()
        except OSError:
            return path.expanduser()
    if is_mutation_artifact_path(path):
        suggested = infer_canonical_repo_root(path, require_git_remote=require_git_remote)
        if suggested is not None:
            return suggested
    return path.expanduser()


def infer_canonical_repo_root(path: Path, *, require_git_remote: bool = False) -> Path | None:
    """Resolve mutation sandbox paths back to the real repository root when possible."""
    from_mutation_record = _source_repo_from_mutation_path(path)
    if from_mutation_record is not None and is_valid_canonical_repo_root(
        from_mutation_record,
        require_git_remote=require_git_remote,
    ):
        return from_mutation_record.resolve()

    truncated = _truncate_before_agent_artifacts(path)
    if truncated is not None and is_valid_canonical_repo_root(
        truncated,
        require_git_remote=require_git_remote,
    ):
        return truncated.resolve()

    from aethos_core.runtime.workspace_diagnostics import repo_root

    runtime_root = repo_root()
    if is_valid_canonical_repo_root(runtime_root, require_git_remote=require_git_remote):
        return runtime_root.resolve()

    return None


def is_valid_canonical_repo_root(path: Path, *, require_git_remote: bool = False) -> bool:
    if not path.is_dir():
        return False
    if is_mutation_artifact_path(path):
        return False
    if not (path / ".git").exists():
        return False
    markers = ("aethos_core", "pyproject.toml", "web", "tests")
    if not any((path / marker).exists() for marker in markers):
        return False
    if require_git_remote and not _git_remote_origin(path):
        return False
    return True


def _truncate_before_agent_artifacts(path: Path) -> Path | None:
    parts = path.resolve().parts
    for idx, part in enumerate(parts):
        if part == "data" and idx + 1 < len(parts) and parts[idx + 1] == "agent_artifacts":
            if idx == 0:
                return None
            return Path(*parts[:idx])
    return None


def _source_repo_from_mutation_path(path: Path) -> Path | None:
    normalized = normalize_path_str(path)
    match = re.search(r"mutation_workspaces/(mws-[a-f0-9]+)/repo", normalized, re.I)
    if not match:
        return None
    try:
        from aethos_core.local_workspace.mutation_workspace import get_mutation_workspace

        record = get_mutation_workspace(match.group(1))
        if not record:
            return None
        source = str(record.get("source_repo") or "").strip()
        if not source:
            return None
        candidate = Path(source).expanduser()
        return candidate if candidate.is_dir() else None
    except Exception:
        return None


def _git_remote_origin(repo: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        if out.returncode == 0:
            return (out.stdout or "").strip() or None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None
