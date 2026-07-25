# SPDX-License-Identifier: Apache-2.0
"""Self-improvement orchestration — issue → plan → branch (Phase 9.7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.self_improvement.git.branch_pr import propose_branch
from aethos_core.self_improvement.issues.intake import fetch_github_issues, plan_from_issue_prompt
from aethos_core.self_improvement.planning.planner import plan_for_issue


@dataclass
class SelfImprovementPlanResult:
    ok: bool
    repository: str
    plan: dict[str, Any] = field(default_factory=dict)
    issues: list[dict[str, Any]] = field(default_factory=list)
    branch: dict[str, Any] = field(default_factory=dict)
    detail: str = ""
    execution_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "repository": self.repository,
            "plan": self.plan,
            "issues": self.issues,
            "branch": self.branch,
            "detail": self.detail,
            "execution_enabled": self.execution_enabled,
            "phase": "9.7",
            "merge_allowed": False,
        }


def build_self_improvement_plan(*, repository: str, issue_number: int | None = None) -> SelfImprovementPlanResult:
    repo = (repository or "").strip()
    if not repo:
        return SelfImprovementPlanResult(ok=False, repository="", detail="Repository required.")

    issues_payload = fetch_github_issues(repository=repo, limit=10)
    issues = list(issues_payload.get("issues") or [])
    selected = None
    if issue_number is not None:
        selected = next((i for i in issues if i.get("number") == issue_number), None)
    elif issues:
        selected = issues[0]

    title = str((selected or {}).get("title") or f"Self-improvement for {repo}")
    number = (selected or {}).get("number")
    intake = plan_from_issue_prompt(repository=repo, issue_hint=str(number) if number else None)
    intake.title = title
    if number:
        intake.issue_number = int(number)

    impl = plan_for_issue(issue_title=title)
    branch = propose_branch(repository=repo, issue_number=int(number) if number else None)

    return SelfImprovementPlanResult(
        ok=issues_payload.get("ok", False) or bool(intake.repository),
        repository=repo,
        plan={
            "intake": intake.to_dict(),
            "implementation": impl.to_dict(),
        },
        issues=issues,
        branch=branch.to_dict(),
        detail=(
            "Bounded self-improvement plan composed — human review required before merge."
            if issues_payload.get("ok")
            else str(issues_payload.get("error") or "GitHub issues unavailable — plan is dry-run only.")
        ),
        execution_enabled=False,
    )
