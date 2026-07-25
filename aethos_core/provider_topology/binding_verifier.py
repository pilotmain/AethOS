# SPDX-License-Identifier: Apache-2.0
"""Validate provider source bindings before mutation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.provider_topology.ambiguity_detection import BindingAmbiguity, detect_binding_ambiguity
from aethos_core.provider_topology.provider_relationships import extract_github_repo_references
from aethos_core.provider_topology.source_binding_resolver import resolve_source_binding_for_service


@dataclass
class BindingVerificationResult:
    ok: bool
    service_path: str
    stored_github_repo: str | None = None
    referenced_github_repo: str | None = None
    installation_ok: bool = True
    ambiguity: BindingAmbiguity | None = None
    failure_stage: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "service_path": self.service_path,
            "stored_github_repo": self.stored_github_repo,
            "referenced_github_repo": self.referenced_github_repo,
            "installation_ok": self.installation_ok,
            "ambiguity": self.ambiguity.to_dict() if self.ambiguity else None,
            "failure_stage": self.failure_stage,
            "message": self.message,
        }


def _accessible_github_repos() -> list[str] | None:
    try:
        from aethos_core.providers.github.auth import GitHubAuthAdapter
        from aethos_core.providers.github.api_client import list_repositories

        auth = GitHubAuthAdapter().resolve_best_auth_method(operation="read_repos")
        if not auth.get("credential_id"):
            return None
        token = GitHubAuthAdapter().get_api_token(str(auth["credential_id"]))
        listed = list_repositories(token)
        if not listed.get("ok"):
            return None
        repos = listed.get("repositories") or []
        return [str(r.get("full_name") or "") for r in repos if isinstance(r, dict) and r.get("full_name")]
    except Exception:
        return None


def verify_source_binding(
    *,
    provider: str,
    project: str,
    environment: str,
    service_name: str,
    user_text: str = "",
    accessible_repos: list[str] | None = None,
    operation_type: str | None = None,
) -> BindingVerificationResult:
    from aethos_core.provider_topology.operation_requirement_policy import requires_source_binding

    path = f"{project} / {environment} / {service_name}"
    resolution = resolve_source_binding_for_service(
        provider=provider,
        project=project,
        environment=environment,
        service=service_name,
    )
    if operation_type and not requires_source_binding(provider, operation_type):
        return BindingVerificationResult(
            ok=True,
            service_path=path,
            stored_github_repo=resolution.github_repo,
            message="Source binding not required for this operation.",
        )

    stored_repo = resolution.github_repo
    refs = extract_github_repo_references(user_text)
    referenced = refs[0] if refs else None

    if not stored_repo and not referenced:
        return BindingVerificationResult(ok=True, service_path=path, message="No stored source binding — topology refresh recommended.")

    repos = accessible_repos if accessible_repos is not None else _accessible_github_repos()
    ambiguity = detect_binding_ambiguity(stored_repo=stored_repo, user_text=user_text, accessible_repos=repos)
    if ambiguity:
        return BindingVerificationResult(
            ok=False,
            service_path=path,
            stored_github_repo=stored_repo,
            referenced_github_repo=referenced or ambiguity.referenced_repo,
            installation_ok=False,
            ambiguity=ambiguity,
            failure_stage="source_binding",
            message=ambiguity.message,
        )

    if stored_repo and repos is not None and stored_repo.lower() not in {r.lower() for r in repos}:
        return BindingVerificationResult(
            ok=False,
            service_path=path,
            stored_github_repo=stored_repo,
            referenced_github_repo=referenced,
            installation_ok=False,
            failure_stage="source_binding",
            message=f"No GitHub installation found for repo: {stored_repo}",
        )

    return BindingVerificationResult(
        ok=True,
        service_path=path,
        stored_github_repo=stored_repo,
        referenced_github_repo=referenced,
        installation_ok=True,
        message="Source binding verified.",
    )


def compose_binding_mismatch_reply(result: BindingVerificationResult) -> str:
    stored = result.stored_github_repo or "(none)"
    referenced = result.referenced_github_repo or "(none)"
    lines = [
        "I found a **provider source mismatch**.",
        "",
        "Current runtime binding:",
        f"- Railway service: **{result.service_path}**",
        f"- Stored GitHub repo: **{stored}**",
    ]
    if result.referenced_github_repo and result.referenced_github_repo != result.stored_github_repo:
        lines.extend(["", "You referenced:", f"- **{referenced}**"])
    lines.extend(
        [
            "",
            "I need confirmation before mutation execution because the runtime source relationship may have changed.",
            "",
            "Please confirm the correct repository so I can refresh provider topology and retry the governed operation.",
        ]
    )
    return "\n".join(lines)
