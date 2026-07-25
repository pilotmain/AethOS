# SPDX-License-Identifier: Apache-2.0
"""FIX 125G — GitHub PR creation preflight checks (read-only)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.github_pr_preflight_contract import (
    MAX_PACKAGE_BYTES_FIX_125G,
    MAX_PACKAGE_FILES_FIX_125G,
)
from aethos_core.software_delivery.governed_workspace import (
    workspace_file_path,
    workspace_tree_root,
)


def _certification_mode() -> bool:
    return os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}


def derive_idempotency_key(*, plan_id: str, draft_id: str) -> str:
    raw = f"github_pr_create_v1:{plan_id}:{draft_id}"
    return f"sdgpr-{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def _cert_auth_fixture(*, repository: str) -> dict[str, Any]:
    return {
        "ok": True,
        "auth_state": "validated",
        "repository_access": True,
        "scopes_required": ["repo", "workflow"],
        "scopes_satisfied": True,
        "account_login": "certification-bot",
        "repository": repository,
        "detail": "Certification simulation — auth/scope OK",
    }


def check_github_auth_scope(*, repository: str) -> dict[str, Any]:
    if _certification_mode():
        return _cert_auth_fixture(repository=repository)

    from aethos_core.credentials import get_provider_api_token
    from aethos_core.providers.github.shared.auth_diagnostics import github_discovery_auth_diagnostics

    token = get_provider_api_token(provider="github")
    diag = github_discovery_auth_diagnostics(token, repository=repository)
    auth_state = str(diag.get("auth_state") or "")
    scopes_ok = bool(diag.get("repository_access")) and auth_state in {"validated", "VALIDATED"}
    ok = bool(token) and scopes_ok and auth_state not in {"invalid", "missing", ""}
    return {
        "check": "github_auth_scope",
        "ok": ok,
        "auth_state": diag.get("auth_state"),
        "repository_access": diag.get("repository_access"),
        "scopes_required": ["repo", "workflow (read)"],
        "scopes_satisfied": scopes_ok,
        "account_login": diag.get("account_login"),
        "repository": diag.get("repository") or repository,
        "failure_class": "" if ok else "github_auth_scope",
        "detail": str(diag.get("detail") or "GitHub auth/scope check"),
    }


def check_branch_push_readiness(
    *,
    plan_id: str,
    branch_name: str,
    files_applied: list[str],
) -> dict[str, Any]:
    tree = workspace_tree_root(plan_id=plan_id)
    missing: list[str] = []
    for rel in files_applied:
        path = workspace_file_path(plan_id=plan_id, rel=rel)
        if not path or not path.is_file():
            missing.append(rel)
    ok = bool(branch_name) and bool(files_applied) and not missing and tree.is_dir()
    return {
        "check": "branch_push_readiness",
        "ok": ok,
        "branch_name": branch_name,
        "workspace_tree": str(tree),
        "files_ready": len(files_applied) - len(missing),
        "missing_in_workspace": missing,
        "git_push_performed": False,
        "failure_class": "" if ok else "branch_push_not_ready",
        "detail": "Workspace tree ready for future push (125H)" if ok else "Branch/workspace not ready",
    }


def check_diff_package_size(*, plan_id: str, files_applied: list[str]) -> dict[str, Any]:
    total_bytes = 0
    for rel in files_applied:
        path = workspace_file_path(plan_id=plan_id, rel=rel)
        if path and path.is_file():
            total_bytes += path.stat().st_size
    file_count = len(files_applied)
    ok = file_count <= MAX_PACKAGE_FILES_FIX_125G and total_bytes <= MAX_PACKAGE_BYTES_FIX_125G
    return {
        "check": "diff_package_size",
        "ok": ok,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "max_files": MAX_PACKAGE_FILES_FIX_125G,
        "max_bytes": MAX_PACKAGE_BYTES_FIX_125G,
        "failure_class": "" if ok else "package_too_large",
        "detail": f"{file_count} files, {total_bytes} bytes",
    }


def check_protected_branch_policy(
    *,
    repository: str,
    branch_name: str,
    default_branch: str = "main",
) -> dict[str, Any]:
    if _certification_mode():
        return {
            "check": "protected_branch_policy",
            "ok": True,
            "default_branch": default_branch,
            "target_branch": default_branch,
            "feature_branch": branch_name,
            "default_branch_protected": True,
            "direct_push_to_default_blocked": True,
            "failure_class": "",
            "detail": "Certification: default branch treated as protected",
        }

    owner, _, repo = repository.partition("/")
    protected = False
    detail = "Could not confirm branch protection via API"
    if owner and repo:
        from aethos_core.credentials import get_provider_api_token
        from aethos_core.providers.github.api_client import request_github

        token = get_provider_api_token(provider="github")
        if token:
            resp = request_github(
                token,
                "GET",
                f"/repos/{owner}/{repo}/branches/{default_branch}/protection",
            )
            if resp.get("ok"):
                protected = True
                detail = f"`{default_branch}` has branch protection rules"
            elif int(resp.get("status_code") or 0) == 404:
                protected = False
                detail = f"No protection API record for `{default_branch}` (may still have rules)"

    ok = bool(branch_name) and branch_name != default_branch
    return {
        "check": "protected_branch_policy",
        "ok": ok,
        "default_branch": default_branch,
        "target_branch": default_branch,
        "feature_branch": branch_name,
        "default_branch_protected": protected,
        "direct_push_to_default_blocked": True,
        "failure_class": "" if ok else "protected_branch_violation",
        "detail": detail if ok else "Feature branch must not target protected default directly",
    }


def build_mutation_preview(
    *,
    repository: str,
    branch_name: str,
    draft: dict[str, Any],
    idempotency_key: str,
) -> dict[str, Any]:
    return {
        "fix_125h_branch_push": {
            "enabled": False,
            "actions": [
                f"Create/update branch `{branch_name}` on {repository}",
                "Push workspace tree commit (governed scope only)",
            ],
            "mutations": ["git_ref_update"],
        },
        "fix_125i_open_pr": {
            "enabled": False,
            "actions": [
                f"Open PR: {draft.get('title', '')}",
                f"Head: `{branch_name}` → base: `main`",
            ],
            "mutations": ["github_pull_request_create"],
        },
        "idempotency_key": idempotency_key,
        "mutation_performed_in_125g": False,
    }


def build_rollback_cleanup_plan(
    *,
    plan_id: str,
    branch_name: str,
    idempotency_key: str,
) -> dict[str, Any]:
    return {
        "rollback_steps": [
            "Do not merge PR if verification regresses",
            f"Delete remote branch `{branch_name}` if push occurred (125H rollback)",
            "Restore workspace from snapshot (125D rollback command)",
            f"Invalidate idempotency lock `{idempotency_key}` if partial apply",
        ],
        "cleanup_targets": [
            f"workspace:{plan_id}",
            f"branch:{branch_name}",
            "github_pr:draft_only_until_125i",
        ],
        "infra_lane_note": "No Railway/production deploy from software delivery lane",
    }


def build_pr_final_review(*, draft: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": draft.get("title"),
        "title_length": len(str(draft.get("title") or "")),
        "body_length": len(str(draft.get("body") or "")),
        "checklist_items": len(draft.get("checklist") or []),
        "human_review_requirements": list(draft.get("human_review_requirements") or []),
        "review_required": True,
    }


def run_github_pr_preflight_checks(
    *,
    plan: dict[str, Any],
    draft: dict[str, Any],
    branch: dict[str, Any],
    application: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    plan_id = str(plan.get("plan_id") or "")
    draft_id = str(draft.get("draft_id") or "")
    repository = str(plan.get("repository") or "")
    branch_name = str(branch.get("branch_name") or draft.get("branch_name") or "")
    files_applied = list(application.get("files_applied") or draft.get("files") or [])
    default_branch = "main"

    readiness_blockers: list[str] = []
    if str(verification.get("status") or "") != "passed":
        readiness_blockers.append("workspace_verification_not_passed")
    if not draft_id:
        readiness_blockers.append("pr_draft_missing")

    checks: list[dict[str, Any]] = [
        {
            "check": "pr_creation_readiness_gate",
            "ok": not readiness_blockers,
            "blockers": readiness_blockers,
            "failure_class": "" if not readiness_blockers else "readiness_blocked",
            "detail": "Readiness gate passed" if not readiness_blockers else ", ".join(readiness_blockers),
        }
    ]

    if readiness_blockers:
        return {
            "ok": False,
            "checks": checks,
            "classification": {
                "status": "failed",
                "failure_class": "readiness_blocked",
                "summary": "PR creation preflight blocked at readiness gate",
            },
            "idempotency_key": derive_idempotency_key(plan_id=plan_id, draft_id=draft_id or "none"),
        }

    idem = derive_idempotency_key(plan_id=plan_id, draft_id=draft_id)
    checks.append(check_github_auth_scope(repository=repository))
    checks.append(
        check_branch_push_readiness(
            plan_id=plan_id,
            branch_name=branch_name,
            files_applied=files_applied,
        )
    )
    checks.append(check_diff_package_size(plan_id=plan_id, files_applied=files_applied))
    checks.append(
        check_protected_branch_policy(
            repository=repository,
            branch_name=branch_name,
            default_branch=default_branch,
        )
    )
    pr_review = build_pr_final_review(draft=draft)
    checks.append(
        {
            "check": "pr_title_body_review",
            "ok": bool(pr_review.get("title")) and int(pr_review.get("body_length") or 0) > 0,
            "review": pr_review,
            "failure_class": "",
            "detail": f"title {pr_review.get('title_length')} chars, body {pr_review.get('body_length')} chars",
        }
    )
    mutation_preview = build_mutation_preview(
        repository=repository,
        branch_name=branch_name,
        draft=draft,
        idempotency_key=idem,
    )
    checks.append(
        {
            "check": "mutation_preview",
            "ok": True,
            "preview": mutation_preview,
            "detail": "125H push + 125I PR preview recorded (no mutation in 125G)",
        }
    )

    failures = [c for c in checks if not c.get("ok")]
    status = "preflight_passed" if not failures else "preflight_failed"
    return {
        "ok": status == "preflight_passed",
        "checks": checks,
        "classification": {
            "status": status,
            "failure_class": failures[0].get("failure_class", "") if failures else "",
            "failure_count": len(failures),
            "summary": "GitHub PR creation preflight passed"
            if status == "preflight_passed"
            else f"Preflight failed ({len(failures)} check(s))",
        },
        "idempotency_key": idem,
        "mutation_preview": mutation_preview,
        "rollback_cleanup_plan": build_rollback_cleanup_plan(
            plan_id=plan_id,
            branch_name=branch_name,
            idempotency_key=idem,
        ),
        "pr_final_review": pr_review,
    }
