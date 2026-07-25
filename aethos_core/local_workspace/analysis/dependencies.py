# SPDX-License-Identifier: Apache-2.0
"""Dependency intelligence — readonly manifest + bounded audit scanners."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any


def analyze_dependencies(repo: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    risks: list[str] = []
    vulnerabilities: list[dict[str, Any]] = []

    npm = _scan_npm(repo)
    if npm:
        audit = _run_npm_audit(repo, npm.get("manifest_dir") or repo)
        if audit:
            npm["audit"] = audit
            vuln_count = int(audit.get("vulnerabilities_total") or 0)
            if vuln_count:
                risks.append(f"npm audit reported {vuln_count} vulnerability entries")
                vulnerabilities.extend(audit.get("top_advisories") or [])
        outdated = _detect_outdated_npm(npm.get("dependencies") or {})
        if outdated:
            npm["outdated_preview"] = outdated
            risks.append(f"{len(outdated)} npm dependencies use loose or stale version ranges")
        findings.append(npm)
        if npm.get("duplicate_lockfiles"):
            risks.append("Multiple package-lock files detected")
        if len(npm.get("dependencies") or {}) > 80:
            risks.append("Large npm dependency surface")

    py = _scan_python(repo)
    if py:
        pip_audit = _run_pip_audit(repo)
        if pip_audit:
            py["pip_audit"] = pip_audit
            if pip_audit.get("vulnerabilities"):
                risks.append(f"pip-audit reported {len(pip_audit['vulnerabilities'])} issues")
                vulnerabilities.extend(pip_audit["vulnerabilities"][:5])
        findings.append(py)
        if len(py.get("dependencies") or []) > 60:
            risks.append("Large Python dependency surface")

    severity = "low"
    if vulnerabilities or len(risks) >= 3:
        severity = "high"
    elif risks:
        severity = "medium"

    return {
        "ok": True,
        "repo": str(repo),
        "findings": findings,
        "risk_summary": risks or ["No high-severity dependency risks detected in manifest scan"],
        "vulnerabilities": vulnerabilities[:10],
        "severity": severity,
        "read_only": True,
    }


def format_dependency_report(analysis: dict[str, Any]) -> str:
    lines = [
        "# Dependency audit (readonly)",
        "",
        f"**Repo:** `{analysis.get('repo')}`",
        f"**Severity:** {analysis.get('severity')}",
        "",
        "## Risks",
    ]
    for risk in analysis.get("risk_summary") or []:
        lines.append(f"- {risk}")
    for vuln in analysis.get("vulnerabilities") or []:
        lines.append(f"- **Vuln:** {vuln.get('name') or vuln.get('id') or vuln}")
    for block in analysis.get("findings") or []:
        lines.extend(["", f"### {block.get('ecosystem')}", f"- Manifest: `{block.get('manifest')}`"])
        audit = block.get("audit") or block.get("pip_audit")
        if audit:
            lines.append(f"- Scanner: `{audit.get('scanner')}` — {audit.get('summary') or 'completed'}")
        deps = block.get("dependencies")
        if isinstance(deps, dict):
            preview = list(deps.items())[:12]
            for name, ver in preview:
                lines.append(f"- `{name}` → {ver}")
            if len(deps) > 12:
                lines.append(f"- … and {len(deps) - 12} more")
        elif isinstance(deps, list):
            for name in deps[:12]:
                lines.append(f"- `{name}`")
        outdated = block.get("outdated_preview") or []
        if outdated:
            lines.append(f"- Outdated/stale preview: {', '.join(outdated[:8])}")
    lines.append("")
    lines.append("*Scanners are bounded readonly subprocess calls — no package installs.*")
    return "\n".join(lines)


def _scan_npm(repo: Path) -> dict[str, Any] | None:
    for candidate in (repo / "web" / "package.json", repo / "package.json"):
        if not candidate.is_file():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        deps = {**dict(data.get("dependencies") or {}), **dict(data.get("devDependencies") or {})}
        lockfiles = [str(p.relative_to(repo)) for p in repo.glob("**/package-lock.json")][:5]
        return {
            "ecosystem": "npm",
            "manifest": str(candidate.relative_to(repo)),
            "manifest_dir": str(candidate.parent),
            "dependencies": deps,
            "duplicate_lockfiles": len(lockfiles) > 1,
            "lockfiles": lockfiles,
        }
    return None


def _scan_python(repo: Path) -> dict[str, Any] | None:
    req = repo / "requirements.txt"
    if req.is_file():
        lines = [ln.strip() for ln in req.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
        return {"ecosystem": "pip", "manifest": "requirements.txt", "dependencies": lines}
    pyproject = repo / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8")
        deps = re.findall(r'^[\w-]+(?:\[[^\]]+\])?\s*=\s*"[^"]+"', text, re.M)
        return {"ecosystem": "poetry/pyproject", "manifest": "pyproject.toml", "dependencies": deps[:40]}
    return None


def _run_npm_audit(repo: Path, manifest_dir: str | Path) -> dict[str, Any] | None:
    cwd = Path(manifest_dir)
    lock = cwd / "package-lock.json"
    if not lock.is_file():
        return None
    try:
        proc = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if not proc.stdout:
            return {"scanner": "npm audit", "ok": False, "summary": (proc.stderr or "no output")[:200]}
        data = json.loads(proc.stdout)
        meta = data.get("metadata", {}).get("vulnerabilities") or {}
        total = sum(int(meta.get(k) or 0) for k in ("info", "low", "moderate", "high", "critical"))
        advisories = []
        for name, adv in (data.get("vulnerabilities") or {}).items():
            if isinstance(adv, dict):
                advisories.append({"name": name, "severity": adv.get("severity"), "via": adv.get("via")})
            if len(advisories) >= 5:
                break
        return {
            "scanner": "npm audit",
            "ok": True,
            "vulnerabilities_total": total,
            "summary": f"{total} npm audit entries",
            "top_advisories": advisories,
        }
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def _run_pip_audit(repo: Path) -> dict[str, Any] | None:
    req = repo / "requirements.txt"
    if not req.is_file() and not (repo / "pyproject.toml").is_file():
        return None
    try:
        proc = subprocess.run(
            ["pip-audit", "--format", "json", "-r", str(req)] if req.is_file() else ["pip-audit", "--format", "json"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=25,
            check=False,
        )
        if proc.returncode not in (0, 1) or not proc.stdout.strip():
            return None
        rows = json.loads(proc.stdout)
        vulns = []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    vulns.append({"name": row.get("name"), "id": row.get("id"), "fix_versions": row.get("fix_versions")})
        return {"scanner": "pip-audit", "ok": True, "vulnerabilities": vulns[:10], "summary": f"{len(vulns)} pip-audit findings"}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None


def _detect_outdated_npm(deps: dict[str, str]) -> list[str]:
    stale: list[str] = []
    for name, ver in deps.items():
        v = str(ver)
        if v in ("*", "latest") or v.startswith("git+"):
            stale.append(name)
        elif re.match(r"^\^0\.", v):
            stale.append(name)
        if len(stale) >= 12:
            break
    return stale
