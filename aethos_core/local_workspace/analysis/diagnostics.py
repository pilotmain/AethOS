# SPDX-License-Identifier: Apache-2.0
"""Repo diagnostics — CI/CD, TODO/debt hotspots."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_TODO_RX = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.I)


def analyze_diagnostics(repo: Path) -> dict[str, Any]:
    workflows = _scan_github_workflows(repo)
    todos = _scan_todo_hotspots(repo)
    return {
        "ok": True,
        "repo": str(repo),
        "ci_cd": workflows,
        "technical_debt": todos,
        "read_only": True,
    }


def analyze_test_state(repo: Path) -> dict[str, Any]:
    scripts = {}
    manifest = None
    for candidate in (repo / "web" / "package.json", repo / "package.json"):
        if candidate.is_file():
            try:
                import json

                data = json.loads(candidate.read_text(encoding="utf-8"))
                scripts = dict(data.get("scripts") or {})
                manifest = str(candidate.relative_to(repo))
                break
            except (OSError, json.JSONDecodeError):
                pass
    pytest_present = (repo / "tests").is_dir() or bool(list(repo.glob("test_*.py")))
    vitest_present = "test" in scripts or "vitest" in str(scripts)
    workflows = _scan_test_workflows(repo)
    pytest_collect = _pytest_collect_only(repo) if pytest_present else None
    return {
        "ok": True,
        "repo": str(repo),
        "pytest_present": pytest_present,
        "frontend_tests": vitest_present,
        "test_scripts": {k: v for k, v in scripts.items() if "test" in k.lower()},
        "frontend_manifest": manifest,
        "ci_test_workflows": workflows,
        "pytest_collect": pytest_collect,
        "note": "Readonly scan — governed execution required for live test runs.",
        "read_only": True,
    }


def format_test_report(analysis: dict[str, Any]) -> str:
    lines = [
        "# Test intelligence (readonly)",
        "",
        f"**Repo:** `{analysis.get('repo')}`",
        f"**Pytest:** {'yes' if analysis.get('pytest_present') else 'no'}",
        f"**Frontend tests:** {'yes' if analysis.get('frontend_tests') else 'no'}",
        "",
        "## Test scripts",
    ]
    scripts = analysis.get("test_scripts") or {}
    if scripts:
        for k, v in scripts.items():
            lines.append(f"- `{k}` → `{v}`")
    else:
        lines.append("- (none detected in package.json)")
    workflows = analysis.get("ci_test_workflows") or []
    if workflows:
        lines.extend(["", "## CI test workflows"])
        for wf in workflows:
            lines.append(f"- `{wf}`")
    collect = analysis.get("pytest_collect") or {}
    if collect.get("ok"):
        lines.extend(["", "## Pytest collection", f"- Collected tests: {collect.get('count', 0)}"])
        for err in collect.get("errors") or []:
            lines.append(f"- **Collection error:** {err}")
    elif collect and collect.get("error"):
        lines.append(f"\nPytest collection unavailable: {collect.get('error')}")
    return "\n".join(lines)


def format_workflow_report(diagnostics: dict[str, Any]) -> str:
    ci = diagnostics.get("ci_cd") or {}
    lines = [
        "# Workflow / CI analysis (readonly)",
        "",
        f"**Repo:** `{diagnostics.get('repo')}`",
        f"**Workflows present:** {'yes' if ci.get('present') else 'no'}",
        "",
        "## GitHub Actions",
    ]
    for wf in ci.get("workflows") or []:
        lines.append(f"- `{wf}`")
    debt = diagnostics.get("technical_debt") or {}
    hotspots = debt.get("hotspots") or []
    if hotspots:
        lines.extend(["", "## Technical debt hotspots"])
        for h in hotspots[:5]:
            lines.append(f"- `{h.get('path')}` — {h.get('markers')} markers")
    return "\n".join(lines)


def _scan_test_workflows(repo: Path) -> list[str]:
    wf_dir = repo / ".github" / "workflows"
    if not wf_dir.is_dir():
        return []
    hits: list[str] = []
    for path in sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if "pytest" in text or "vitest" in text or "npm test" in text or "jest" in text:
            hits.append(path.name)
    return hits


def _pytest_collect_only(repo: Path) -> dict[str, Any]:
    import subprocess

    if not (repo / "tests").is_dir() and not list(repo.glob("test_*.py")):
        return {"ok": False, "error": "no pytest tests dir"}
    try:
        proc = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        out = (proc.stdout or "") + "\n" + (proc.stderr or "")
        count = 0
        errors: list[str] = []
        for line in out.splitlines():
            if " error" in line.lower() or line.startswith("ERROR"):
                errors.append(line.strip()[:200])
            if " test" in line.lower() and "collected" in line.lower():
                import re

                m = re.search(r"(\d+)\s+test", line)
                if m:
                    count = int(m.group(1))
        if proc.returncode not in (0, 5) and not count:
            return {"ok": False, "error": (out.strip() or "pytest collect failed")[:240], "errors": errors[:5]}
        return {"ok": True, "count": count, "errors": errors[:5]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}


def _scan_github_workflows(repo: Path) -> dict[str, Any]:
    wf_dir = repo / ".github" / "workflows"
    if not wf_dir.is_dir():
        return {"present": False, "workflows": []}
    files = sorted(wf_dir.glob("*.yml")) + sorted(wf_dir.glob("*.yaml"))
    names = [f.name for f in files]
    return {"present": bool(names), "workflows": names, "count": len(names)}


def _scan_todo_hotspots(repo: Path, *, limit: int = 8) -> dict[str, Any]:
    hotspots: list[dict[str, Any]] = []
    scanned = 0
    for path in repo.rglob("*"):
        if scanned > 400:
            break
        if not path.is_file():
            continue
        if path.suffix not in {".py", ".ts", ".tsx", ".js", ".md"}:
            continue
        if "node_modules" in path.parts or ".git" in path.parts:
            continue
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        count = len(_TODO_RX.findall(text))
        if count:
            hotspots.append({"path": str(path.relative_to(repo)), "markers": count})
    hotspots.sort(key=lambda h: h["markers"], reverse=True)
    return {"hotspots": hotspots[:limit], "files_scanned": scanned}
