# SPDX-License-Identifier: Apache-2.0
"""Readonly git intelligence."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _git(repo: Path, *args: str, timeout: float = 12.0) -> dict[str, Any]:
    allowed = {"status", "branch", "remote", "log", "rev-parse", "diff", "show-ref"}
    if not args or args[0] not in allowed:
        raise PermissionError(f"Git command not allowed: {args}")
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        out = ((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")).strip()
        return {"ok": proc.returncode == 0, "output": out, "read_only": True}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc), "read_only": True}


def git_status_snapshot(repo: Path) -> dict[str, Any]:
    branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    status = _git(repo, "status", "--porcelain=v1", "-b")
    ahead_behind = _parse_ahead_behind(status.get("output") or "")
    modified, untracked = _count_status_lines(status.get("output") or "")
    return {
        "ok": bool(branch.get("ok") and status.get("ok")),
        "branch": (branch.get("output") or "").strip() or None,
        "status_short": status.get("output") or "",
        "modified_count": modified,
        "untracked_count": untracked,
        "ahead": ahead_behind.get("ahead", 0),
        "behind": ahead_behind.get("behind", 0),
        "read_only": True,
        "mutating": False,
    }


def git_branches(repo: Path) -> dict[str, Any]:
    local = _git(repo, "branch", "--format=%(refname:short)")
    return {"ok": local.get("ok"), "branches": [b for b in (local.get("output") or "").splitlines() if b.strip()]}


def git_recent_commits(repo: Path, *, limit: int = 10) -> dict[str, Any]:
    out = _git(repo, "log", f"-{limit}", "--oneline")
    lines = [ln for ln in (out.get("output") or "").splitlines() if ln.strip()]
    return {"ok": out.get("ok"), "commits": lines}


def git_diff_summary(repo: Path) -> dict[str, Any]:
    stat = _git(repo, "diff", "--stat")
    shortstat = _git(repo, "diff", "--shortstat")
    return {
        "ok": stat.get("ok"),
        "diff_stat": stat.get("output") or "",
        "shortstat": shortstat.get("output") or "",
        "read_only": True,
    }


def _count_status_lines(text: str) -> tuple[int, int]:
    modified = 0
    untracked = 0
    for line in text.splitlines():
        if line.startswith("##"):
            continue
        if line.startswith("??"):
            untracked += 1
        elif line.strip():
            modified += 1
    return modified, untracked


def _parse_ahead_behind(status_text: str) -> dict[str, int]:
    for line in status_text.splitlines():
        if not line.startswith("##"):
            continue
        if "[" not in line:
            return {"ahead": 0, "behind": 0}
        bracket = line.split("[", 1)[-1].rstrip("]")
        ahead = behind = 0
        for part in bracket.split(","):
            part = part.strip()
            if part.endswith("ahead"):
                try:
                    ahead = int(part.split()[0])
                except ValueError:
                    pass
            if part.endswith("behind"):
                try:
                    behind = int(part.split()[0])
                except ValueError:
                    pass
        return {"ahead": ahead, "behind": behind}
    return {"ahead": 0, "behind": 0}
