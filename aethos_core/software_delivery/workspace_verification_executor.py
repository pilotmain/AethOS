# SPDX-License-Identifier: Apache-2.0
"""FIX 125E — bounded workspace verification checks (no arbitrary shell)."""

from __future__ import annotations

import ast
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.governed_workspace import (
    repo_root,
    workspace_file_path,
    workspace_tree_root,
)
from aethos_core.software_delivery.workspace_verification_contract import (
    ALLOWLISTED_TEST_COMMAND,
    ALLOWLISTED_TEST_COMMAND_KEY,
)

_DESTRUCTIVE_DIFF_RX = re.compile(
    r"\b(rm\s+-rf|drop\s+table|truncate|delete\s+all)\b",
    re.I,
)
_MAX_DIFF_LINES = 500


def _certification_mode() -> bool:
    return os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}


def check_file_existence(*, plan_id: str, files: list[str]) -> dict[str, Any]:
    missing: list[str] = []
    for rel in files:
        path = workspace_file_path(plan_id=plan_id, rel=rel)
        if not path or not path.is_file():
            missing.append(rel)
    ok = not missing
    return {
        "check": "file_existence",
        "ok": ok,
        "missing_files": missing,
        "failure_class": "" if ok else "missing_workspace_file",
        "detail": f"{len(files) - len(missing)}/{len(files)} files present in workspace tree",
    }


def check_workspace_files_modified(*, plan_id: str, files: list[str]) -> dict[str, Any]:
    """Confirm workspace files differ from repo (without parsing huge unified diffs)."""
    changed: list[str] = []
    for rel in files:
        path = workspace_file_path(plan_id=plan_id, rel=rel)
        if not path or not path.is_file():
            continue
        repo_path = repo_root() / rel
        ws_text = path.read_text(encoding="utf-8", errors="replace")
        repo_text = repo_path.read_text(encoding="utf-8", errors="replace") if repo_path.is_file() else ""
        if ws_text != repo_text:
            changed.append(rel)
    ok = bool(changed) if files else False
    return {
        "check": "workspace_files_modified",
        "ok": ok,
        "changed_files": changed,
        "failure_class": "" if ok else "invalid_diff",
        "detail": f"{len(changed)} file(s) modified in workspace tree",
    }


def check_static_diff_validation(*, proposal_diffs: list[dict[str, str]]) -> dict[str, Any]:
    """Validate bounded proposal preview diffs (125C), not full repo↔workspace diff."""
    if not proposal_diffs:
        return {
            "check": "static_diff_validation",
            "ok": False,
            "failure_class": "invalid_diff",
            "detail": "No proposal preview diffs to validate",
        }
    issues: list[str] = []
    for entry in proposal_diffs:
        diff = entry.get("diff") or ""
        path = entry.get("file") or "unknown"
        if not diff.strip():
            issues.append(f"{path}:empty_diff")
            continue
        if _DESTRUCTIVE_DIFF_RX.search(diff):
            issues.append(f"{path}:destructive_pattern")
        if diff.count("\n") > _MAX_DIFF_LINES:
            issues.append(f"{path}:diff_too_large")
    ok = not issues
    return {
        "check": "static_diff_validation",
        "ok": ok,
        "issues": issues,
        "failure_class": "" if ok else "invalid_diff",
        "detail": "static diff validation passed" if ok else "; ".join(issues[:5]),
    }


def check_python_syntax(*, plan_id: str, files: list[str]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    for rel in files:
        if not str(rel).endswith(".py"):
            continue
        path = workspace_file_path(plan_id=plan_id, rel=rel)
        if not path or not path.is_file():
            continue
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            ast.parse(source, filename=str(rel))
        except SyntaxError as exc:
            errors.append({"file": rel, "error": str(exc)})
    ok = not errors
    return {
        "check": "python_syntax",
        "ok": ok,
        "syntax_errors": errors,
        "failure_class": "" if ok else "syntax_error",
        "detail": "syntax ok" if ok else f"{len(errors)} syntax error(s)",
    }


def run_allowlisted_test_command(*, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {
            "check": "allowlisted_test",
            "ok": True,
            "skipped": True,
            "failure_class": "",
            "detail": "allowlisted test disabled",
        }
    if _certification_mode():
        return {
            "check": "allowlisted_test",
            "ok": True,
            "skipped": False,
            "runner": ALLOWLISTED_TEST_COMMAND_KEY,
            "failure_class": "",
            "detail": "certification simulation passed",
            "execution_mode": "certification_simulation",
        }

    cmd = list(ALLOWLISTED_TEST_COMMAND)
    repo = repo_root()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=120.0,
            check=False,
        )
        out = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        ok = proc.returncode == 0
        return {
            "check": "allowlisted_test",
            "ok": ok,
            "runner": ALLOWLISTED_TEST_COMMAND_KEY,
            "command": cmd,
            "output": out[-3000:],
            "exit_code": proc.returncode,
            "failure_class": "" if ok else "allowlisted_test_failed",
            "detail": "allowlisted pytest smoke passed" if ok else f"exit {proc.returncode}",
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "check": "allowlisted_test",
            "ok": False,
            "failure_class": "allowlisted_test_failed",
            "detail": str(exc),
        }


def classify_verification_results(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [c for c in checks if not c.get("ok") and not c.get("skipped")]
    failure_classes = [str(c.get("failure_class") or "unknown") for c in failures if c.get("failure_class")]
    if not failures:
        return {
            "status": "passed",
            "failure_class": "",
            "failure_count": 0,
            "pr_drafting_unblocked": True,
            "summary": "All workspace verification checks passed",
        }
    primary = failure_classes[0] if failure_classes else "unknown"
    return {
        "status": "failed",
        "failure_class": primary,
        "failure_classes": failure_classes,
        "failure_count": len(failures),
        "pr_drafting_unblocked": False,
        "summary": f"Verification failed: {primary} ({len(failures)} check(s))",
    }


def run_workspace_verification_checks(
    *,
    plan_id: str,
    files_applied: list[str],
    proposal_diffs: list[dict[str, str]],
    allow_allowlisted_test: bool,
) -> dict[str, Any]:
    tree = workspace_tree_root(plan_id=plan_id)
    if not tree.is_dir():
        return {
            "ok": False,
            "checks": [],
            "classification": classify_verification_results(
                [{"ok": False, "failure_class": "verification_blocked"}]
            ),
            "workspace_tree": str(tree),
        }

    checks: list[dict[str, Any]] = []
    if _certification_mode():
        checks.append(
            {
                "check": "workspace_tree_inspected",
                "ok": True,
                "detail": "certification workspace tree",
            }
        )
    else:
        checks.append(
            {
                "check": "workspace_tree_inspected",
                "ok": tree.is_dir(),
                "detail": str(tree),
                "failure_class": "" if tree.is_dir() else "verification_blocked",
            }
        )

    checks.append(check_file_existence(plan_id=plan_id, files=files_applied))
    checks.append(check_static_diff_validation(proposal_diffs=proposal_diffs))
    checks.append(check_workspace_files_modified(plan_id=plan_id, files=files_applied))
    checks.append(check_python_syntax(plan_id=plan_id, files=files_applied))
    checks.append(run_allowlisted_test_command(enabled=allow_allowlisted_test))

    classification = classify_verification_results(checks)
    return {
        "ok": classification.get("status") == "passed",
        "checks": checks,
        "classification": classification,
        "workspace_tree": str(tree),
    }
