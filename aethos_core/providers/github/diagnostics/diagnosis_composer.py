# SPDX-License-Identifier: Apache-2.0
"""Compose operator-facing GitHub live diagnostics."""

from __future__ import annotations

from typing import Any


def compose_github_live_diagnosis_reply(evidence: dict[str, Any], *, operation: str = "live_diagnosis") -> str:
    repo_name = str(evidence.get("repository") or "unknown")
    lines = [f"GitHub live diagnostics for **{repo_name}**:"]

    repo = dict(evidence.get("repo") or {})
    branch = dict(evidence.get("branch") or {})
    if repo.get("ok"):
        lines.extend(
            [
                "",
                "Repository state:",
                f"- Default branch: **{repo.get('default_branch') or '—'}**",
                f"- Visibility: **{'private' if repo.get('private') else 'public'}**",
                f"- Last push: `{repo.get('pushed_at') or '—'}`",
            ]
        )
    if branch.get("ok"):
        lines.extend(
            [
                f"- Active branch head: `{branch.get('sha', '')[:12]}` on **{branch.get('branch')}**",
                f"- Branch protected: **{'yes' if branch.get('protected') else 'no'}**",
            ]
        )

    divergence = dict(evidence.get("divergence") or {})
    if operation in {"live_diagnosis", "branch_divergence", "repo_status"} and divergence.get("ok"):
        lines.extend(
            [
                "",
                "Branch divergence:",
                f"- Compare `{divergence.get('base')}`...`{divergence.get('head')}` → "
                f"**{divergence.get('ahead_by', 0)} ahead**, **{divergence.get('behind_by', 0)} behind**",
                f"- Compare status: `{divergence.get('status') or 'unknown'}`",
            ]
        )
    if operation in {"live_diagnosis", "branch_divergence", "repo_status"} and evidence.get("local_changes_note"):
        lines.extend(["", "Uncommitted change detection:", f"- {evidence['local_changes_note']}"])

    if operation in {"live_diagnosis", "workflows", "workflow_logs", "workflow_failures", "failed_checks", "repo_status"}:
        _append_workflow_failures(lines, evidence)

    if operation in {"live_diagnosis", "failed_checks", "pr_status"}:
        _append_failed_checks(lines, evidence)

    if operation in {"live_diagnosis", "recent_commits", "repo_status"}:
        commits = dict(evidence.get("commits") or {})
        if commits.get("ok") and commits.get("commits"):
            lines.extend(["", "Recent commits:"])
            for commit in commits["commits"][:5]:
                lines.append(f"- `{commit.get('sha')}` {commit.get('message')} ({commit.get('author')})")

    if operation in {"live_diagnosis", "pr_status"}:
        _append_pull_requests(lines, evidence)

    if operation in {"live_diagnosis", "releases"}:
        _append_releases(lines, evidence)

    correlation = dict(evidence.get("deploy_correlation") or {})
    if correlation.get("lines"):
        lines.extend(["", "Deploy correlation:"])
        for item in correlation["lines"]:
            lines.append(f"- {item}")

    lines.extend(["", "Findings:", *_compose_findings(evidence)])
    lines.extend(["", "Next readonly evidence step:", _next_readonly_step(evidence, operation=operation)])
    lines.extend(
        [
            "",
            "Governed mutation available: **workflow rerun only** (requires approval). Push/commit/PR mutations are not enabled yet.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def _append_workflow_failures(lines: list[str], evidence: dict[str, Any]) -> None:
    diagnostic = dict(evidence.get("workflow_diagnostic") or {})
    jobs = dict(evidence.get("workflow_jobs") or {})
    lines.extend(["", "Workflow failures:"])
    if not diagnostic.get("ok"):
        lines.append(f"- Workflow diagnostics unavailable: {diagnostic.get('error') or 'unknown error'}")
        return
    latest = dict(diagnostic.get("latest_failed_run") or {})
    if not latest:
        lines.append("- No failed workflow runs in recent GitHub Actions history.")
        return
    lines.append(
        f"- Latest failure: **{latest.get('name') or 'workflow'}** run #{latest.get('run_number')} on `{latest.get('head_branch')}`"
    )
    failed_job = diagnostic.get("likely_failure_job") or (
        (jobs.get("failed_jobs") or [{}])[0].get("name") if jobs.get("failed_jobs") else None
    )
    failed_step = diagnostic.get("likely_failure_step")
    if failed_job:
        detail = f"failed job **{failed_job}**"
        if failed_step:
            detail += f" at step **{failed_step}**"
        lines.append(f"- Failure point: {detail}")
    if failed_job or failed_step:
        summary = f"Workflow failed in job **{failed_job or 'unknown'}**"
        if failed_step:
            summary += f" at step **{failed_step}**"
        lines.append(f"- Operator summary: {summary}")
    elif latest.get("conclusion"):
        lines.append(f"- Conclusion: `{latest.get('conclusion')}` — inspect workflow logs for the failing step output.")


def _append_failed_checks(lines: list[str], evidence: dict[str, Any]) -> None:
    checks = dict(evidence.get("checks") or {})
    lines.extend(["", "Failed checks:"])
    if not checks.get("ok"):
        lines.append(f"- Check runs unavailable: {checks.get('error') or 'unknown error'}")
        return
    failed = list(checks.get("checks") or [])
    if not failed:
        lines.append("- No failed check runs on the latest ref.")
        return
    for check in failed[:5]:
        lines.append(f"- **{check.get('name')}** ({check.get('conclusion')})")


def _append_pull_requests(lines: list[str], evidence: dict[str, Any]) -> None:
    pulls = dict(evidence.get("pull_requests") or {})
    lines.extend(["", "Pull request status:"])
    if not pulls.get("ok"):
        lines.append(f"- PR lookup unavailable: {pulls.get('error') or 'unknown error'}")
        return
    open_prs = list(pulls.get("pull_requests") or [])
    if not open_prs:
        lines.append("- No open pull requests.")
        return
    for pr in open_prs[:3]:
        lines.append(
            f"- PR #{pr.get('number')}: **{pr.get('title')}** `{pr.get('head')}` → `{pr.get('base')}` "
            f"(mergeable: {pr.get('mergeable_state') or 'unknown'})"
        )


def _append_releases(lines: list[str], evidence: dict[str, Any]) -> None:
    releases = dict(evidence.get("releases") or {})
    lines.extend(["", "Releases / tags:"])
    if not releases.get("ok"):
        lines.append("- Release/tag lookup unavailable.")
        return
    latest_release = releases.get("latest_release")
    latest_tag = releases.get("latest_tag")
    if latest_release:
        lines.append(f"- Latest release: **{latest_release.get('name') or latest_release.get('tag_name')}**")
    if latest_tag:
        lines.append(f"- Latest tag: `{latest_tag}`")
    if not latest_release and not latest_tag:
        lines.append("- No releases or tags found.")


def _compose_findings(evidence: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    diagnostic = dict(evidence.get("workflow_diagnostic") or {})
    checks = dict(evidence.get("checks") or {})
    divergence = dict(evidence.get("divergence") or {})

    if diagnostic.get("latest_failed_run"):
        findings.append("GitHub CI is failing on the latest workflow run — deploy should be treated as blocked until checks pass.")
    elif checks.get("failed_count"):
        findings.append(f"{checks['failed_count']} failing check run(s) detected on the latest ref.")
    else:
        findings.append("No recent workflow/check failures detected in GitHub evidence.")

    if divergence.get("ok") and (int(divergence.get("behind_by") or 0) > 0):
        findings.append("The inspected branch is behind its compare ref — merge/rebase may be required before deploy.")
    if not findings:
        findings.append("GitHub evidence is healthy on the inspected surface; continue with provider deploy logs if production is still failing.")
    return [f"- {item}" for item in findings]


def _next_readonly_step(evidence: dict[str, Any], *, operation: str) -> str:
    diagnostic = dict(evidence.get("workflow_diagnostic") or {})
    checks = dict(evidence.get("checks") or {})
    correlation = dict(evidence.get("deploy_correlation") or {})

    if diagnostic.get("latest_failed_run") or checks.get("failed_count"):
        return (
            "Read workflow job logs for the failing step, then inspect the linked Vercel/Railway deployment "
            "that consumed the failing commit SHA."
        )
    if correlation.get("deploy_related_failures"):
        return "Compare the failing GitHub workflow commit SHA against the latest Railway/Vercel deployment revision."
    if operation == "pr_status":
        return "Inspect PR checks and the latest workflow run for the PR head branch."
    if operation == "releases":
        return "Verify the latest release tag against the production deployment currently running."
    return "If production is still unhealthy, fetch Railway/Vercel deployment logs for the commit currently deployed."
