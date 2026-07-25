# SPDX-License-Identifier: Apache-2.0
"""Engineering validation — block unrestricted shell."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

_BLOCKED_SHELL = frozenset({"bash", "sh", "zsh", "fish", "/bin/bash", "/bin/sh"})


def run_engineering_validation_step(
    repo: Path,
    *,
    patch_plan: dict[str, Any] | None = None,
    workspace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = patch_plan or {}
    sandbox = workspace or {}
    repo_path = Path(sandbox.get("sandbox_path") or repo)
    steps = plan.get("validation_steps") or ["pytest (scoped)"]
    result = run_engineering_validation(repo_path, validation_steps=steps)
    if workspace:
        workspace["validation_status"] = result.get("validation_status")
    return result


def run_engineering_validation(
    repo: Path,
    *,
    validation_steps: list[str] | None = None,
    test_paths: list[str] | None = None,
    timeout_sec: float = 90.0,
) -> dict[str, Any]:
    """Run bounded validation — pytest subset, optional npm build."""
    from aethos_core.engineering.validation_runtime import (
        run_engineering_validation as _run,
    )

    steps = validation_steps or ["pytest (scoped)"]
    if _contains_unrestricted_shell(steps):
        return {
            "ok": False,
            "validation_status": "validation_failed",
            "error": "unrestricted_shell_blocked",
            "tests_executed": [],
            "pass_count": 0,
            "fail_count": 1,
        }
    return _run(repo, validation_steps=steps, test_paths=test_paths, timeout_sec=timeout_sec)


def _contains_unrestricted_shell(steps: list[str]) -> bool:
    joined = " ".join(steps).lower()
    return any(tok in joined for tok in ("unrestricted shell", "arbitrary bash", "docker compose up"))


def _run_pytest_blocked_check(cmd: list[str]) -> bool:
    if not cmd:
        return False
    exe = cmd[0].lower()
    return exe in _BLOCKED_SHELL
