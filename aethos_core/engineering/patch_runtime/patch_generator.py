# SPDX-License-Identifier: Apache-2.0
"""Patch generator — bounded deterministic edits."""

from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any

from aethos_core.engineering.patch_runtime.patch_scope import validate_patch_scope

_PILOT_EXECUTION_LOG_HEADING = "## Pilot Execution Log"


def generate_governed_patches(
    repo: Path,
    *,
    user_request: str,
    task: dict[str, Any] | None = None,
    target_files: list[str] | None = None,
) -> dict[str, Any]:
    task = task or {}
    files = target_files or task.get("affected_files") or []
    scope = validate_patch_scope(allowed_files=files, requested_files=files, user_request=user_request)
    if not scope.get("ok"):
        return {"ok": False, "scope": scope, "patches": [], "unified_diffs": []}

    kind = str(task.get("kind") or "general_engineering")
    patches: list[dict[str, Any]] = []
    diffs: list[dict[str, str]] = []

    for rel in files[:12]:
        path = repo / rel
        if not path.is_file():
            continue
        try:
            original = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        new_content = _apply_kind_patch(rel, original, kind=kind, user_request=user_request, task=task)
        if new_content == original:
            continue
        diff = "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
        )
        patches.append({"file": rel, "new_content": new_content, "kind": kind})
        diffs.append({"file": rel, "diff": diff, "lines_changed": diff.count("\n+") + diff.count("\n-")})

    return {
        "ok": bool(patches),
        "scope": scope,
        "patches": patches,
        "unified_diffs": diffs,
        "files_patched": [p["file"] for p in patches],
    }


def _apply_kind_patch(rel: str, original: str, *, kind: str, user_request: str, task: dict[str, Any]) -> str:
    marker = "AethOS governed patch (Phase 9.8F)"
    if marker in original:
        return original

    if kind == "workflow_fix" and "workflow_resolution" in rel:
        addition = (
            "\n\n# AethOS governed patch (Phase 9.8F): align readonly/mutation workflow rerun resolution.\n"
            "GOVERNED_RERUN_RESOLUTION_SUBSTRATE = \"readonly_mutation_converged\"\n"
        )
        return original.rstrip() + addition + "\n"

    if kind == "deployment_diagnostics" and "deployment_intelligence" in rel:
        addition = (
            "\n\n# AethOS governed patch (Phase 9.8F): deployment diagnostics correlation marker.\n"
            "GOVERNED_DEPLOYMENT_DIAGNOSTICS_DEPTH = \"timeline_correlation_v1\"\n"
        )
        return original.rstrip() + addition + "\n"

    if kind == "dependency_modernization" and rel.endswith("package.json"):
        return original

    if kind == "bounded_issue_scope" and rel.endswith(".md"):
        return _apply_bounded_doc_scope_patch(original, user_request=user_request, task=task)

    if kind in ("governed_patch", "general_engineering"):
        fix = task.get("proposed_fix") or user_request[:120]
        addition = f"\n\n# {marker}: {fix}\n"
        if rel.endswith(".py"):
            return original.rstrip() + addition
    return original


def _apply_bounded_doc_scope_patch(original: str, *, user_request: str, task: dict[str, Any]) -> str:
    if _PILOT_EXECUTION_LOG_HEADING in original:
        return original
    combined = (
        f"{user_request}\n{task.get('proposed_fix') or ''}\n{task.get('raw_request') or ''}\n"
        f"{task.get('title') or ''}"
    ).lower()
    if "pilot execution log" not in combined:
        return original
    section = (
        "\n\n## Pilot Execution Log\n\n"
        "| Date | Issue | Stages Reached | PR | Operator Effort Notes |\n"
        "|------|-------|----------------|-----|----------------------|\n"
        "| 2026-05-29 | pilotmain/AethOS#1 | pilot validation | TBD | "
        "First governed dogfood pilot placeholder |\n"
    )
    return original.rstrip() + section


def apply_patches_to_workspace(
    workspace: dict[str, Any],
    patches: list[dict[str, Any]],
) -> dict[str, Any]:
    from aethos_core.local_workspace.mutation_workspace import stage_planned_patch

    applied: list[str] = []
    errors: list[dict[str, str]] = []
    for patch in patches:
        result = stage_planned_patch(
            workspace,
            file_path=str(patch["file"]),
            new_content=str(patch["new_content"]),
        )
        if result.get("ok"):
            applied.append(str(patch["file"]))
        else:
            errors.append({"file": str(patch["file"]), "error": str(result.get("error") or "failed")})
    return {"ok": not errors, "applied": applied, "errors": errors, "workspace": workspace}
