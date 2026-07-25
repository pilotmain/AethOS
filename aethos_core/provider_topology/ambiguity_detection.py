# SPDX-License-Identifier: Apache-2.0
"""Detect conflicting or ambiguous provider source bindings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.provider_topology.provider_relationships import extract_github_repo_references


@dataclass
class BindingAmbiguity:
    kind: str
    message: str
    stored_repo: str | None = None
    referenced_repo: str | None = None
    candidates: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "message": self.message,
            "stored_repo": self.stored_repo,
            "referenced_repo": self.referenced_repo,
            "candidates": list(self.candidates or []),
        }


def detect_binding_ambiguity(
    *,
    stored_repo: str | None,
    user_text: str,
    accessible_repos: list[str] | None = None,
) -> BindingAmbiguity | None:
    refs = extract_github_repo_references(user_text)
    if stored_repo and refs:
        for ref in refs:
            if ref.lower() != stored_repo.lower():
                return BindingAmbiguity(
                    kind="repo_mismatch",
                    message="Referenced GitHub repository differs from stored binding.",
                    stored_repo=stored_repo,
                    referenced_repo=ref,
                )

    if stored_repo and accessible_repos is not None:
        norm = stored_repo.lower()
        if norm not in {r.lower() for r in accessible_repos}:
            alt = [r for r in accessible_repos if stored_repo.split("/")[-1].lower() in r.lower()]
            if len(alt) == 1:
                return BindingAmbiguity(
                    kind="installation_mismatch",
                    message="Stored repository is not installed, but a similarly named repository exists.",
                    stored_repo=stored_repo,
                    referenced_repo=alt[0],
                    candidates=alt,
                )
            if refs:
                for ref in refs:
                    if ref.lower() in {r.lower() for r in accessible_repos}:
                        return BindingAmbiguity(
                            kind="repo_mismatch",
                            message="Stored repository installation missing; user referenced an accessible repository.",
                            stored_repo=stored_repo,
                            referenced_repo=ref,
                        )
            return BindingAmbiguity(
                kind="installation_missing",
                message=f"No GitHub installation found for stored repo: {stored_repo}",
                stored_repo=stored_repo,
                candidates=accessible_repos[:5],
            )
    return None
