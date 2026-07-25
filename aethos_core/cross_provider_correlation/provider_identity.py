# SPDX-License-Identifier: Apache-2.0
"""GitHub provider identity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderIdentity:
    provider: str
    repo: str = ""
    branch: str = ""
    commit_sha: str = ""
    status: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "repo": self.repo,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "status": self.status,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> ProviderIdentity | None:
        if not raw:
            return None
        return cls(
            provider=str(raw.get("provider") or "github"),
            repo=str(raw.get("repo") or ""),
            branch=str(raw.get("branch") or ""),
            commit_sha=str(raw.get("commit_sha") or ""),
            status=str(raw.get("status") or ""),
            metadata=dict(raw.get("metadata") or {}),
        )
