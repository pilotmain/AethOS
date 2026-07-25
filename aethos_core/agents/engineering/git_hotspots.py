# SPDX-License-Identifier: Apache-2.0
"""Git hotspot analysis — unstable commits, hot files, TODO concentration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from aethos_core.local_workspace.git.intelligence import git_diff_summary, git_recent_commits, git_status_snapshot

_TODO_RX = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.I)
_HOT_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs"}


def run_git_hotspot_analysis(repo: Path) -> dict[str, Any]:
    git = git_status_snapshot(repo)
    commits = git_recent_commits(repo, limit=12)
    diff = git_diff_summary(repo)
    hot_files = _scan_hot_files(repo)
    todo_hits = _scan_todo_concentration(repo)
    unstable = _unstable_commit_signals(commits.get("commits") or [])

    return {
        "ok": True,
        "repo": str(repo),
        "git": git,
        "recent_commits": commits.get("commits") or [],
        "diff_summary": diff.get("shortstat") or "",
        "hot_files": hot_files[:15],
        "todo_concentration": todo_hits[:12],
        "unstable_commits": unstable,
        "risk_signals": _hotspot_signals(git, hot_files, todo_hits, unstable),
    }


def format_git_hotspot_report(analysis: dict[str, Any]) -> str:
    lines = [
        "# Git hotspot analysis (readonly)",
        "",
        f"**Branch:** {((analysis.get('git') or {}).get('branch')) or 'unknown'}",
        f"**Modified:** {(analysis.get('git') or {}).get('modified_count', 0)} · "
        f"**Untracked:** {(analysis.get('git') or {}).get('untracked_count', 0)}",
        "",
        "## Recent commits",
    ]
    for c in (analysis.get("recent_commits") or [])[:8]:
        lines.append(f"- {c}")
    hot = analysis.get("hot_files") or []
    if hot:
        lines.extend(["", "## Hot files (recent change density)"])
        for row in hot[:8]:
            lines.append(f"- `{row.get('path')}` — {row.get('reason')}")
    todos = analysis.get("todo_concentration") or []
    if todos:
        lines.extend(["", "## TODO / FIXME concentration"])
        for row in todos[:6]:
            lines.append(f"- `{row.get('path')}` — {row.get('count')} markers")
    unstable = analysis.get("unstable_commits") or []
    if unstable:
        lines.extend(["", "## Unstable commit signals"])
        for u in unstable[:4]:
            lines.append(f"- {u}")
    return "\n".join(lines)


def _scan_hot_files(repo: Path, *, limit: int = 20) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or path.suffix not in _HOT_EXTENSIONS:
            continue
        rel = str(path.relative_to(repo))
        if any(part.startswith(".") or part in {"node_modules", "__pycache__", ".next"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        lines = len(text.splitlines())
        if lines > 400:
            rows.append({"path": rel, "reason": f"large module ({lines} lines)", "weight": 2})
        elif lines > 200:
            rows.append({"path": rel, "reason": f"medium module ({lines} lines)", "weight": 1})
    rows.sort(key=lambda r: r.get("weight", 0), reverse=True)
    return rows[:limit]


def _scan_todo_concentration(repo: Path, *, max_files: int = 40) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    scanned = 0
    for path in sorted(repo.rglob("*")):
        if scanned >= max_files:
            break
        if not path.is_file() or path.suffix not in _HOT_EXTENSIONS:
            continue
        if any(part.startswith(".") or part in {"node_modules", "__pycache__"} for part in path.parts):
            continue
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        count = len(_TODO_RX.findall(text))
        if count >= 3:
            hits.append({"path": str(path.relative_to(repo)), "count": count})
    hits.sort(key=lambda h: h["count"], reverse=True)
    return hits


def _unstable_commit_signals(commits: list[str]) -> list[str]:
    signals: list[str] = []
    keywords = ("fix", "revert", "hotfix", "crash", "fail", "broken", "rollback")
    for line in commits[:8]:
        low = line.lower()
        if any(k in low for k in keywords):
            signals.append(line)
    return signals


def _hotspot_signals(
    git: dict[str, Any],
    hot_files: list[dict[str, Any]],
    todos: list[dict[str, Any]],
    unstable: list[str],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if int(git.get("modified_count") or 0) > 15:
        signals.append({"kind": "hotspot", "weight": 1, "detail": "high working tree churn"})
    if hot_files:
        signals.append({"kind": "hotspot", "weight": 1, "detail": f"{len(hot_files)} complexity hotspots"})
    if todos:
        signals.append({"kind": "hotspot", "weight": 1, "detail": "TODO/FIXME concentration detected"})
    if unstable:
        signals.append({"kind": "repeated_failure", "weight": 1, "detail": "recent fix/revert commit pattern"})
    return signals
