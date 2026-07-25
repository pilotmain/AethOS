# SPDX-License-Identifier: Apache-2.0
"""Branch + PR manager — no automatic merge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class BranchPlan:
    repository: str
    branch_name: str
    create_pr: bool = True
    merge_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "branch_name": self.branch_name,
            "create_pr": self.create_pr,
            "merge_allowed": self.merge_allowed,
            "requires_approval": True,
        }


def propose_branch(*, repository: str, issue_number: int | None = None) -> BranchPlan:
    suffix = f"issue-{issue_number}" if issue_number else "self-improvement"
    return BranchPlan(repository=repository, branch_name=f"aethos/{suffix}")
