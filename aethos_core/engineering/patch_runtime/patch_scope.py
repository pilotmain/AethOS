# SPDX-License-Identifier: Apache-2.0
"""Patch scope governance — allowed/blocked paths."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from aethos_core.engineering.patch_runtime.patch_limits import MAX_PATCH_FILES

_BLOCKED_RX = re.compile(
    r"(^|/)\.env($|/|\.)|(^|/)secrets/|(^|/)\.ssh/|(^|/)id_rsa|/etc/|(^|/)\.git/|node_modules/",
    re.I,
)
_DESTRUCTIVE_RX = re.compile(r"\b(delete all|rm -rf|drop table|truncate)\b", re.I)


def validate_patch_scope(
    *,
    allowed_files: list[str],
    requested_files: list[str],
    user_request: str = "",
) -> dict[str, Any]:
    blocked: list[str] = []
    for f in requested_files:
        if _BLOCKED_RX.search(f):
            blocked.append(f)
    over = len(requested_files) > MAX_PATCH_FILES
    out_of_scope = [f for f in requested_files if allowed_files and f not in allowed_files]
    destructive = bool(_DESTRUCTIVE_RX.search(user_request or ""))
    ok = not blocked and not over and not out_of_scope and not destructive
    return {
        "ok": ok,
        "scope_valid": ok,
        "blocked_paths": blocked,
        "out_of_scope": out_of_scope,
        "over_file_limit": over,
        "destructive_request": destructive,
        "files_allowed": allowed_files,
        "files_requested": requested_files,
        "max_files": MAX_PATCH_FILES,
    }


def assert_path_in_repo(repo: Path, rel: str) -> bool:
    try:
        target = (repo / rel).resolve()
        root = repo.resolve()
        return str(target).startswith(str(root))
    except (OSError, ValueError):
        return False
