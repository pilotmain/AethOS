# SPDX-License-Identifier: Apache-2.0
"""Readonly workspace intelligence orchestration."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from aethos_core.local_workspace.analysis.architecture import analyze_architecture, format_architecture_report
from aethos_core.local_workspace.analysis.dependencies import analyze_dependencies, format_dependency_report
from aethos_core.local_workspace.analysis.diagnostics import (
    analyze_diagnostics,
    analyze_test_state,
    format_test_report,
    format_workflow_report,
)
from aethos_core.local_workspace.artifacts.store import store_workspace_artifact
from aethos_core.local_workspace.canonical_path import (
    iter_repo_files_limited,
    path_should_be_skipped_for_scan,
)
from aethos_core.local_workspace.git.intelligence import (
    git_branches,
    git_diff_summary,
    git_recent_commits,
    git_status_snapshot,
)
from aethos_core.local_workspace.memory.engineering_memory import hydrate_workspace_memory, record_engineering_event
from aethos_core.local_workspace.registry import find_workspace_by_hint, list_workspaces, resolve_workspace_path
from aethos_core.local_workspace.scanner import read_package_scripts, scan_workspace_stack
from aethos_core.local_workspace.session_context import resolve_operational_hint
from aethos_core.security.secret_redaction import redact_dotenv_values, redact_text


def run_workspace_scan(repo: Path, *, workspace_id: str | None = None) -> dict[str, Any]:
    stack = scan_workspace_stack(repo)
    git = git_status_snapshot(repo)
    architecture = analyze_architecture(repo)
    dependencies = analyze_dependencies(repo)
    diagnostics = analyze_diagnostics(repo)
    tests = analyze_test_state(repo)
    payload = {
        "stack": stack,
        "git_status": git,
        "architecture": architecture,
        "dependencies": dependencies,
        "diagnostics": diagnostics,
        "tests": tests,
    }
    artifact = store_workspace_artifact(
        artifact_type="local_repo_scan",
        workspace_id=workspace_id,
        repo_path=str(repo),
        payload=payload,
        summary=f"Workspace scan — branch {git.get('branch') or 'unknown'}",
    )
    record_engineering_event(
        event="workspace_scan",
        workspace_id=workspace_id,
        repo_path=str(repo),
        detail=artifact.get("summary"),
    )
    if workspace_id:
        from aethos_core.local_workspace.registry import get_workspace

        ws = get_workspace(workspace_id)
        if ws:
            hydrate_workspace_memory(ws, payload)
    return {"ok": True, "repo": str(repo), "artifact": artifact, "scan": payload}


def run_git_status_report(*, hint: str | None = None, session_id: str = "default") -> dict[str, Any]:
    repo = _repo_from_hint(hint, session_id=session_id)
    git = git_status_snapshot(repo)
    branches = git_branches(repo)
    commits = git_recent_commits(repo)
    diff = git_diff_summary(repo)
    ws = find_workspace_by_hint(hint or repo.name)
    artifact = store_workspace_artifact(
        artifact_type="git_status_snapshot",
        workspace_id=ws.get("workspace_id") if ws else None,
        repo_path=str(repo),
        payload={"git": git, "branches": branches, "commits": commits, "diff": diff},
        summary=f"Git status — {git.get('branch')}",
    )
    report = _format_git_report(repo, git, branches, commits, diff)
    return {"ok": True, "report": report, "artifact": artifact, "git": git}


def run_architecture_report(*, hint: str | None = None, session_id: str = "default") -> dict[str, Any]:
    repo = _repo_from_hint(hint, session_id=session_id)
    analysis = analyze_architecture(repo)
    ws = find_workspace_by_hint(hint or repo.name)
    artifact = store_workspace_artifact(
        artifact_type="architecture_analysis",
        workspace_id=ws.get("workspace_id") if ws else None,
        repo_path=str(repo),
        payload=analysis,
        summary="Architecture analysis",
    )
    if ws:
        hydrate_workspace_memory(ws, {"architecture": analysis})
    return {"ok": True, "report": format_architecture_report(analysis), "artifact": artifact, "analysis": analysis}


def run_dependency_report(*, hint: str | None = None, session_id: str = "default") -> dict[str, Any]:
    repo = _repo_from_hint(hint, session_id=session_id)
    analysis = analyze_dependencies(repo)
    ws = find_workspace_by_hint(hint or repo.name)
    artifact = store_workspace_artifact(
        artifact_type="dependency_audit",
        workspace_id=ws.get("workspace_id") if ws else None,
        repo_path=str(repo),
        payload=analysis,
        summary=f"Dependency audit — severity {analysis.get('severity')}",
    )
    return {"ok": True, "report": format_dependency_report(analysis), "artifact": artifact, "analysis": analysis}


def run_test_report(*, hint: str | None = None, session_id: str = "default") -> dict[str, Any]:
    repo = _repo_from_hint(hint, session_id=session_id)
    analysis = analyze_test_state(repo)
    ws = find_workspace_by_hint(hint or repo.name)
    artifact = store_workspace_artifact(
        artifact_type="test_failure_report",
        workspace_id=ws.get("workspace_id") if ws else None,
        repo_path=str(repo),
        payload=analysis,
        summary="Test intelligence scan",
    )
    return {"ok": True, "report": format_test_report(analysis), "artifact": artifact, "analysis": analysis}


def run_workflow_report(*, hint: str | None = None, session_id: str = "default") -> dict[str, Any]:
    repo = _repo_from_hint(hint, session_id=session_id)
    diagnostics = analyze_diagnostics(repo)
    ws = find_workspace_by_hint(hint or repo.name)
    artifact = store_workspace_artifact(
        artifact_type="workflow_analysis",
        workspace_id=ws.get("workspace_id") if ws else None,
        repo_path=str(repo),
        payload=diagnostics,
        summary=f"Workflow analysis — {len((diagnostics.get('ci_cd') or {}).get('workflows') or [])} workflows",
    )
    return {"ok": True, "report": format_workflow_report(diagnostics), "artifact": artifact, "diagnostics": diagnostics}


def _repo_from_hint(hint: str | None, *, session_id: str = "default") -> Path:
    from aethos_core.local_workspace.portfolio import resolve_repo_reference

    resolved = resolve_repo_reference(hint or "", session_id=session_id)
    path = str(resolved.get("resolved_path") or resolved.get("path") or "").strip()
    if path:
        return Path(path)
    fallback = resolve_operational_hint(hint, session_id=session_id)
    ws = find_workspace_by_hint(fallback) if fallback else None
    if ws and ws.get("path"):
        return Path(str(ws["path"]))
    return resolve_workspace_path(fallback)


def _format_git_report(repo: Path, git: dict, branches: dict, commits: dict, diff: dict) -> str:
    lines = [
        "# Local git intelligence (readonly)",
        "",
        f"**Path:** `{repo}`",
        f"**Branch:** {git.get('branch') or 'unknown'}",
        f"**Modified:** {git.get('modified_count', 0)} · **Untracked:** {git.get('untracked_count', 0)}",
        f"**Ahead/behind:** {git.get('ahead', 0)}/{git.get('behind', 0)}",
        "",
        "## Status",
        "```",
        git.get("status_short") or "(clean)",
        "```",
        "",
        "## Recent commits",
    ]
    for c in commits.get("commits") or []:
        lines.append(f"- {c}")
    if diff.get("shortstat"):
        lines.extend(["", "## Diff summary", "```", diff.get("shortstat") or "", "```"])
    lines.extend(["", "**Writes blocked:** commit · push · merge · branch delete"])
    return "\n".join(lines)


# --- Governed read-only local-repo tools (path-allowlisted to registered workspaces) ---
#
# These power the agent's repo_overview/repo_list/repo_read/repo_grep tools. They are
# READ-ONLY, never execute or write, and reject any path outside a registered Local
# Workspace. File content is redacted (.env values + generic secret patterns) before it
# is returned to the model. Size/time caps keep a single review turn bounded.

_REPO_READ_MAX_BYTES = 64_000
_REPO_LIST_MAX_ENTRIES = 500
_REPO_GREP_MAX_RESULTS = 120
_REPO_GREP_TIMEOUT_S = 15
_REPO_GREP_SUFFIXES = (
    ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yaml", ".yml", ".toml",
    ".md", ".txt", ".sh", ".env", ".cfg", ".ini", ".go", ".rs", ".java", ".sql",
)
_OVERVIEW_COUNT_SUFFIXES = _REPO_GREP_SUFFIXES + (".html", ".css", ".scss")


def _workspace_registration_hint() -> str:
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if is_hosted_deployment():
        return (
            "On hosted AethOS, local laptop paths cannot be read. For GitHub repos ask me to review "
            "owner/repo via the GitHub API (connect GitHub in Mission Control → Advanced settings → Credentials). "
            "Local workspace registration is only for self-hosted installs with disk access."
        )
    return "Register the repo in Mission Control → Code workspaces first."


def _registered_roots() -> list[Path]:
    roots: list[Path] = []
    for row in list_workspaces():
        raw = str(row.get("path") or "").strip()
        if not raw:
            continue
        try:
            roots.append(Path(raw).expanduser().resolve())
        except OSError:
            continue
    try:
        from aethos_core.remote_workspace.registry import github_workspace_paths

        roots.extend(github_workspace_paths())
    except Exception:  # noqa: BLE001 — optional hosted substrate
        pass
    return roots


def _is_within(target: Path, root: Path) -> bool:
    if target == root:
        return True
    try:
        return target.is_relative_to(root)
    except (ValueError, AttributeError):
        return False


def _allowlist_blocker(target: Path, roots: list[Path]) -> dict[str, Any] | None:
    if not any(_is_within(target, root) for root in roots):
        return {
            "ok": False,
            "error": "path_not_in_registered_workspace",
            "path": str(target),
            "registered": [str(r) for r in roots],
            "hint": "Only registered workspaces are readable. " + _workspace_registration_hint(),
        }
    if path_should_be_skipped_for_scan(target):
        return {"ok": False, "error": "path_excluded", "path": str(target)}
    return None


def _resolve_in_workspace(path_or_hint: str, *, want: str = "any") -> tuple[Path | None, dict[str, Any] | None]:
    """Resolve a path/hint to an absolute path that is inside a registered workspace."""
    raw = (path_or_hint or "").strip()
    if not raw:
        return None, {"ok": False, "error": "path_required"}
    roots = _registered_roots()
    if not roots:
        return None, {
            "ok": False,
            "error": "no_registered_workspaces",
            "hint": _workspace_registration_hint(),
        }

    target: Path | None = None
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        target = candidate
    else:
        ws = find_workspace_by_hint(raw)
        if ws and ws.get("path"):
            target = Path(str(ws["path"]))
        else:
            for root in roots:
                rel = (root / raw)
                if rel.exists():
                    target = rel
                    break
            if target is None:
                target = roots[0] / raw

    try:
        target = target.resolve()
    except OSError:
        pass

    blocker = _allowlist_blocker(target, roots)
    if blocker is not None:
        return None, blocker
    if want == "file" and not target.is_file():
        return None, {"ok": False, "error": "file_not_found", "path": str(target)}
    if want == "dir" and not target.is_dir():
        return None, {"ok": False, "error": "dir_not_found", "path": str(target)}
    return target, None


def _resolve_workspace_root(workspace: str | None) -> tuple[Path | None, dict[str, Any] | None]:
    roots = _registered_roots()
    if not roots:
        return None, {
            "ok": False,
            "error": "no_registered_workspaces",
            "hint": _workspace_registration_hint(),
        }
    if workspace and str(workspace).strip():
        ws = find_workspace_by_hint(str(workspace))
        if ws and ws.get("path"):
            repo = Path(str(ws["path"])).expanduser().resolve()
            blocker = _allowlist_blocker(repo, roots)
            return (None, blocker) if blocker else (repo, None)
        return None, {
            "ok": False,
            "error": "workspace_not_registered",
            "workspace": str(workspace),
            "registered": [str(r) for r in roots],
        }
    return roots[0], None


def repo_read(*, path: str, max_bytes: int | None = None, session_id: str = "default") -> dict[str, Any]:
    """Return file contents (text only, size-capped, secrets redacted)."""
    cap = max(1, min(int(max_bytes or _REPO_READ_MAX_BYTES), _REPO_READ_MAX_BYTES))
    target, err = _resolve_in_workspace(path, want="file")
    if err:
        return err
    try:
        raw_bytes = target.read_bytes()
    except OSError as exc:
        return {"ok": False, "error": "read_failed", "detail": str(exc), "path": str(target)}
    if b"\x00" in raw_bytes[:4096]:
        return {"ok": False, "error": "binary_file_skipped", "path": str(target)}
    truncated = len(raw_bytes) > cap
    content = raw_bytes[:cap].decode("utf-8", errors="replace")
    name = target.name.lower()
    if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
        content = redact_dotenv_values(content)
    content = redact_text(content)
    return {
        "ok": True,
        "tool": "repo_read",
        "path": str(target),
        "bytes": len(raw_bytes),
        "truncated": truncated,
        "content": content,
    }


def repo_list(*, path: str, max_depth: int = 2, session_id: str = "default") -> dict[str, Any]:
    """Return a bounded directory tree (skips .git/node_modules/build dirs)."""
    depth_cap = max(1, min(int(max_depth or 2), 6))
    target, err = _resolve_in_workspace(path, want="dir")
    if err:
        return err
    root_depth = len(target.parts)
    entries: list[str] = []
    truncated = False
    stack = [target]
    while stack and not truncated:
        current = stack.pop()
        try:
            children = sorted(current.iterdir(), key=lambda c: (c.is_file(), c.name.lower()))
        except OSError:
            continue
        for child in children:
            if path_should_be_skipped_for_scan(child):
                continue
            depth = len(child.parts) - root_depth
            if depth > depth_cap:
                continue
            rel = child.relative_to(target)
            if child.is_dir():
                entries.append(f"{rel}/")
                if depth < depth_cap:
                    stack.append(child)
            else:
                entries.append(str(rel))
            if len(entries) >= _REPO_LIST_MAX_ENTRIES:
                truncated = True
                break
    entries.sort()
    return {
        "ok": True,
        "tool": "repo_list",
        "path": str(target),
        "max_depth": depth_cap,
        "count": len(entries),
        "truncated": truncated,
        "entries": entries,
    }


def _ripgrep_matches(search_dir: Path, pattern: str, max_results: int) -> list[str] | None:
    rg = shutil.which("rg")
    if not rg:
        return None
    cmd = [
        rg, "--line-number", "--no-heading", "--color=never",
        "--max-count", str(max_results),
        "-g", "!node_modules", "-g", "!.git", "-g", "!*.min.*",
        "-e", pattern, str(search_dir),
    ]
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=_REPO_GREP_TIMEOUT_S, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode not in (0, 1):  # 1 = no matches (not an error)
        return None
    lines = [ln for ln in (out.stdout or "").splitlines() if ln.strip()]
    return [redact_text(ln) for ln in lines[:max_results]]


def _python_grep(search_dir: Path, pattern: str, max_results: int) -> list[str]:
    try:
        rx = re.compile(pattern)
    except re.error:
        rx = re.compile(re.escape(pattern))
    matches: list[str] = []
    for file in iter_repo_files_limited(search_dir, max_depth=8, suffixes=_REPO_GREP_SUFFIXES):
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if rx.search(line):
                matches.append(redact_text(f"{file}:{lineno}:{line.strip()[:200]}"))
                if len(matches) >= max_results:
                    return matches
    return matches


def repo_grep(*, path: str, pattern: str, max_results: int | None = None, session_id: str = "default") -> dict[str, Any]:
    """ripgrep-style search inside a registered workspace (read-only)."""
    if not (pattern or "").strip():
        return {"ok": False, "error": "pattern_required"}
    cap = max(1, min(int(max_results or _REPO_GREP_MAX_RESULTS), _REPO_GREP_MAX_RESULTS))
    target, err = _resolve_in_workspace(path, want="any")
    if err:
        return err
    search_dir = target if target.is_dir() else target.parent
    matches = _ripgrep_matches(search_dir, pattern, cap)
    engine = "ripgrep"
    if matches is None:
        matches = _python_grep(search_dir, pattern, cap)
        engine = "python"
    return {
        "ok": True,
        "tool": "repo_grep",
        "path": str(target),
        "pattern": pattern,
        "engine": engine,
        "count": len(matches),
        "truncated": len(matches) >= cap,
        "matches": matches,
    }


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _detect_dependencies(repo: Path) -> dict[str, Any]:
    deps: dict[str, Any] = {}
    for pkg in (repo / "package.json", repo / "web" / "package.json"):
        if pkg.is_file():
            data = _read_json(pkg)
            deps["node"] = {
                "manifest": str(pkg.relative_to(repo)),
                "dependencies": sorted((data.get("dependencies") or {}).keys()),
                "dev_dependencies": sorted((data.get("devDependencies") or {}).keys()),
            }
            break
    pyproject = repo / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8")
            block = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, re.S)
            pkgs = re.findall(r'"\s*([A-Za-z0-9][A-Za-z0-9._-]*)', block.group(1)) if block else []
            deps["python"] = {"manifest": "pyproject.toml", "dependencies": sorted(set(pkgs))}
        except OSError:
            pass
    reqs = repo / "requirements.txt"
    if reqs.is_file() and "python" not in deps:
        try:
            lines = [ln.strip() for ln in reqs.read_text(encoding="utf-8").splitlines()]
            names = [re.split(r"[<>=!~\s]", ln)[0] for ln in lines if ln and not ln.startswith("#")]
            deps["python"] = {"manifest": "requirements.txt", "dependencies": sorted(set(n for n in names if n))}
        except OSError:
            pass
    return deps


def _file_stats(repo: Path) -> dict[str, Any]:
    by_ext: dict[str, int] = {}
    total = 0
    for file in iter_repo_files_limited(repo, max_depth=8, suffixes=_OVERVIEW_COUNT_SUFFIXES):
        total += 1
        by_ext[file.suffix] = by_ext.get(file.suffix, 0) + 1
    top = dict(sorted(by_ext.items(), key=lambda kv: kv[1], reverse=True)[:10])
    return {"counted": total, "by_extension": top}


def _detect_tests(repo: Path) -> dict[str, Any]:
    has_tests_dir = any((repo / d).is_dir() for d in ("tests", "test", "__tests__", "web/__tests__"))
    sample = 0
    for file in iter_repo_files_limited(repo, max_depth=8, suffixes=(".py", ".ts", ".tsx", ".js")):
        n = file.name.lower()
        if n.startswith("test_") or "_test." in n or ".test." in n or ".spec." in n:
            sample += 1
            if sample >= 50:
                break
    return {"has_tests_dir": has_tests_dir, "test_file_sample": sample, "present": has_tests_dir or sample > 0}


def _detect_entry_points(repo: Path) -> list[str]:
    candidates = [
        "main.py", "app.py", "manage.py", "wsgi.py", "asgi.py",
        "index.ts", "index.js", "src/index.ts", "src/main.ts", "src/main.tsx",
        "next.config.js", "next.config.ts", "Dockerfile", "docker-compose.yml",
        "pyproject.toml", "package.json", "web/package.json",
    ]
    return [c for c in candidates if (repo / c).exists()]


def repo_overview(*, workspace: str | None = None, session_id: str = "default") -> dict[str, Any]:
    """Quick read-only summary: stack, deps, entry points, file count, test presence."""
    repo, err = _resolve_workspace_root(workspace)
    if err:
        return err
    return {
        "ok": True,
        "tool": "repo_overview",
        "path": str(repo),
        "name": repo.name,
        "stack": scan_workspace_stack(repo),
        "scripts": read_package_scripts(repo).get("scripts") or {},
        "dependencies": _detect_dependencies(repo),
        "files": _file_stats(repo),
        "tests": _detect_tests(repo),
        "entry_points": _detect_entry_points(repo),
        "registered_workspaces": [str(r) for r in _registered_roots()],
    }
