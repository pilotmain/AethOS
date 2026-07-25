# SPDX-License-Identifier: Apache-2.0
"""Patch validation — diff sanity and basic syntax."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def validate_patches(repo: Path, patches: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    for patch in patches:
        rel = str(patch.get("file") or "")
        content = str(patch.get("new_content") or "")
        path = repo / rel
        if rel.endswith(".py"):
            try:
                ast.parse(content)
            except SyntaxError as exc:
                issues.append({"file": rel, "issue": f"python syntax: {exc.msg}"})
        if path.is_file():
            old = path.read_text(encoding="utf-8", errors="replace")
            if len(content) > len(old) * 3 + 500:
                issues.append({"file": rel, "issue": "suspicious size increase"})
    return {"ok": not issues, "issues": issues, "patch_count": len(patches)}
