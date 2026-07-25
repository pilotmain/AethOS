# SPDX-License-Identifier: Apache-2.0
"""FIX 109B — Read-only verification of Railway GitHub source binding state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SourceBindingVerification:
    ok: bool
    verified: bool
    readonly: bool = True
    repository_expected: str = ""
    branch_expected: str = ""
    repository_observed: str = ""
    branch_observed: str = ""
    matches_plan: bool = False
    matches_journal: bool = False
    detail: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verified": self.verified,
            "readonly": self.readonly,
            "repository_expected": self.repository_expected,
            "branch_expected": self.branch_expected,
            "repository_observed": self.repository_observed,
            "branch_observed": self.branch_observed,
            "matches_plan": self.matches_plan,
            "matches_journal": self.matches_journal,
            "detail": self.detail,
            "errors": list(self.errors),
        }


def verify_source_binding_readonly(
    *,
    environment_id: str,
    service_id: str,
    expected_repository: str,
    expected_branch: str,
    journal_binding: dict[str, str] | None = None,
    token: str | None = None,
) -> SourceBindingVerification:
    """
    Compare expected repo/branch against Railway environment config (read-only).

    Never stages, commits, or writes env vars.
    """
    repo_expected = (expected_repository or "").strip()
    branch_expected = (expected_branch or "main").strip()
    if not environment_id or not service_id:
        return SourceBindingVerification(
            ok=False,
            verified=False,
            detail="missing environment_id or service_id",
            errors=["missing_target_ids"],
        )
    if not repo_expected:
        return SourceBindingVerification(
            ok=False,
            verified=False,
            detail="expected repository is required",
            errors=["expected_repository_missing"],
        )

    if not token:
        from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

        token, _source, cred_error = resolve_railway_mutation_credentials()
        if not token:
            return SourceBindingVerification(
                ok=False,
                verified=False,
                detail=cred_error or "Railway credentials unavailable for readonly verification",
                errors=["credentials_unavailable"],
            )

    from aethos_core.providers.railway.greenfield_adapters.source_bind_graphql import (
        read_service_source_binding,
    )
    from aethos_core.providers.railway.greenfield_deployment.git_remote_resolution import (
        normalize_github_repository_slug,
    )

    observed = read_service_source_binding(
        token,
        environment_id=environment_id,
        service_id=service_id,
    )
    if not observed.get("ok"):
        return SourceBindingVerification(
            ok=False,
            verified=False,
            repository_expected=repo_expected,
            branch_expected=branch_expected,
            detail=str(observed.get("detail") or "readonly source read failed"),
            errors=["readonly_read_failed"],
        )

    repo_observed = normalize_github_repository_slug(str(observed.get("repository") or ""))
    branch_observed = str(observed.get("branch") or "").strip() or "main"
    repo_expected_norm = normalize_github_repository_slug(repo_expected)
    matches_plan = repo_observed == repo_expected_norm and branch_observed == branch_expected

    journal_binding = journal_binding or {}
    matches_journal = True
    if journal_binding:
        journal_repo = normalize_github_repository_slug(str(journal_binding.get("repository") or ""))
        matches_journal = (
            journal_repo == repo_observed
            and str(journal_binding.get("branch") or "main").strip() == branch_observed
        )

    verified = bool(observed.get("bound")) and matches_plan and matches_journal
    detail = "source binding verified via readonly environment config" if verified else (
        "source binding mismatch or not yet visible in environment config"
    )
    errors: list[str] = []
    if not observed.get("bound"):
        errors.append("repository_not_bound_in_environment")
    elif not matches_plan:
        errors.append("repository_or_branch_mismatch")
    elif not matches_journal:
        errors.append("journal_binding_mismatch")

    return SourceBindingVerification(
        ok=True,
        verified=verified,
        repository_expected=repo_expected,
        branch_expected=branch_expected,
        repository_observed=repo_observed,
        branch_observed=branch_observed,
        matches_plan=matches_plan,
        matches_journal=matches_journal,
        detail=detail,
        errors=errors,
    )
