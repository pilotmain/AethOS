# SPDX-License-Identifier: Apache-2.0
"""Engineering validation runtime — bounded test/build execution."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


VALIDATION_STATES = frozenset(
    {
        "validation_pending",
        "validation_running",
        "validation_failed",
        "validated",
        "verification_failed",
        "rollback_required",
    }
)


def run_engineering_validation(
    repo: Path,
    *,
    validation_steps: list[str] | None = None,
    test_paths: list[str] | None = None,
    timeout_sec: float = 90.0,
) -> dict[str, Any]:
    """Run bounded validation — pytest subset, optional npm build."""
    steps = validation_steps or ["pytest (scoped)"]
    results: list[dict[str, Any]] = []
    state = "validation_running"
    passed = 0
    failed = 0

    if any("pytest" in s.lower() for s in steps):
        r = _run_pytest(repo, test_paths or _default_test_paths(repo), timeout_sec=timeout_sec)
        results.append(r)
        if r.get("ok"):
            passed += int(r.get("passed") or 0)
        else:
            failed += 1
            state = "validation_failed"

    if state != "validation_failed" and any("npm build" in s.lower() or "vitest" in s.lower() for s in steps):
        r = _run_npm_script(repo, timeout_sec=min(timeout_sec, 120.0))
        results.append(r)
        if not r.get("ok"):
            failed += 1
            state = "validation_failed"

    if state == "validation_running":
        state = "validated"

    return {
        "ok": state == "validated",
        "validation_status": state,
        "tests_executed": results,
        "pass_count": passed,
        "fail_count": failed,
        "validation_confidence": "high" if state == "validated" and passed else "medium" if state == "validated" else "low",
        "build_output": "\n".join((r.get("output") or "")[:500] for r in results),
    }


def _run_pytest(repo: Path, paths: list[str], *, timeout_sec: float) -> dict[str, Any]:
    existing = [str(repo / p) for p in paths if (repo / p).exists()]
    if not existing:
        existing = ["tests"]
    cmd = ["python", "-m", "pytest", *existing[:6], "-q", "--tb=no", "--maxfail=3"]
    try:
        proc = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True, timeout=timeout_sec, check=False)
        out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        ok = proc.returncode == 0
        passed = out.count(" passed") if ok else 0
        return {"ok": ok, "runner": "pytest", "output": out[-4000:], "passed": passed, "exit_code": proc.returncode}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "runner": "pytest", "error": str(exc)}


def _run_npm_script(repo: Path, *, timeout_sec: float) -> dict[str, Any]:
    web = repo / "web"
    if not (web / "package.json").is_file():
        return {"ok": True, "runner": "npm", "skipped": True}
    try:
        proc = subprocess.run(
            ["npm", "run", "build", "--if-present"],
            cwd=str(web),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        return {"ok": proc.returncode == 0, "runner": "npm build", "output": out[-2000:], "exit_code": proc.returncode}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "runner": "npm build", "error": str(exc)}


def _default_test_paths(repo: Path) -> list[str]:
    candidates = [
        "tests/test_phase_98e3_operational_intelligence.py",
        "tests/test_phase_98e2_report_quality.py",
        "tests/test_phase_98e_multi_agent_runtime.py",
    ]
    return [p for p in candidates if (repo / p).is_file()][:3]
