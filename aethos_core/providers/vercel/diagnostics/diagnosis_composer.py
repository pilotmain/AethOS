# SPDX-License-Identifier: Apache-2.0
"""Compose operator-facing Vercel live diagnostics."""

from __future__ import annotations

from typing import Any


def compose_vercel_live_diagnosis_reply(evidence: dict[str, Any], *, operation: str = "live_diagnosis") -> str:
    if evidence.get("error") == "multiple_projects":
        return _compose_projects_clarification(evidence)

    if not evidence.get("ok") and evidence.get("projects") and operation == "projects":
        return _compose_projects_overview(evidence)

    project_name = str(evidence.get("project_name") or "unknown")
    lines = ["Vercel deployment diagnostics", "", f"Project: **{project_name}**"]

    project = dict(evidence.get("project") or {})
    details = dict(project.get("details") or {})
    if details:
        lines.extend(
            [
                f"- Framework: **{details.get('framework') or '—'}**",
                f"- Git repo: **{details.get('repo_link') or '—'}**",
                f"- Production branch: `{details.get('production_branch') or '—'}`",
                f"- Production URL: {details.get('production_url') or '—'}",
            ]
        )

    if operation in {"live_diagnosis", "deployments", "projects", "failed_deployment"}:
        _append_latest_deployment(lines, evidence)

    if operation in {"live_diagnosis", "logs", "failed_deployment"}:
        _append_build_runtime_evidence(lines, evidence)

    if operation in {"live_diagnosis", "domains", "deployments", "failed_deployment"}:
        _append_domain_health(lines, evidence)

    if operation in {"live_diagnosis", "env_metadata"}:
        _append_env_metadata(lines, evidence)

    correlation = dict(evidence.get("github_correlation") or {})
    if correlation.get("lines"):
        lines.extend(["", "GitHub source correlation:"])
        for item in correlation["lines"]:
            lines.append(f"- {item}")

    lines.extend(["", "Findings:", *_compose_findings(evidence)])
    lines.extend(["", "Next readonly evidence step:", _next_readonly_step(evidence, operation=operation)])
    lines.extend(
        [
            "",
            "Readonly inspection only — redeploy, rollback, and env mutations are not enabled on this path.",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def _compose_projects_clarification(evidence: dict[str, Any]) -> str:
    lines = [
        "I can run Vercel live deployment diagnostics read-only, but I need a project target.",
        "",
        "Available projects:",
    ]
    for row in evidence.get("projects") or []:
        if isinstance(row, dict):
            lines.append(f"- **{row.get('name')}** · production `{row.get('latest_production_state') or 'unknown'}`")
    lines.extend(
        [
            "",
            "Which Vercel project should I inspect?",
            'Example: "inspect Vercel deployments for my-app"',
            "",
            "No mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def _compose_projects_overview(evidence: dict[str, Any]) -> str:
    projects = dict(evidence.get("projects") or {})
    lines = ["Vercel project inventory (readonly):", ""]
    for row in projects.get("projects") or []:
        if isinstance(row, dict):
            lines.append(
                f"- **{row.get('name')}** · repo `{row.get('repo_link') or '—'}` · "
                f"production `{row.get('latest_production_state') or 'unknown'}`"
            )
    lines.extend(["", "No mutation has been performed."])
    return "\n".join(lines)


def _append_latest_deployment(lines: list[str], evidence: dict[str, Any]) -> None:
    latest = dict(evidence.get("latest_deployment") or {})
    failed = dict(evidence.get("failed_deployment") or {})
    focus = latest or failed
    heading = "Production deployment:" if latest else "Latest deployment:"
    lines.extend(["", heading])
    if not focus:
        lines.append("- No deployments returned from Vercel API.")
        return
    _append_deployment_details(lines, focus)
    if (
        failed
        and latest
        and failed.get("id") != latest.get("id")
        and str(latest.get("state") or "").lower() in {"ready", "completed"}
    ):
        lines.extend(["", "Most recent failed deployment (historical):"])
        _append_deployment_details(lines, failed)


def _append_deployment_details(lines: list[str], focus: dict[str, Any]) -> None:
    source = "GitHub" if focus.get("branch") or focus.get("commit") else "unknown"
    lines.extend(
        [
            f"- status: **{focus.get('state') or 'unknown'}**",
            f"- created: `{focus.get('created_at') or '—'}`",
            f"- source: **{source}**",
            f"- git commit: `{focus.get('commit') or '—'}`",
            f"- branch: `{focus.get('branch') or '—'}`",
            f"- url: {focus.get('url') or focus.get('inspector_url') or '—'}",
        ]
    )
    if focus.get("error_message"):
        lines.append(f"- error: {str(focus['error_message'])[:240]}")


def _append_build_runtime_evidence(lines: list[str], evidence: dict[str, Any]) -> None:
    build = dict(evidence.get("build_analysis") or {})
    runtime = dict(evidence.get("runtime_analysis") or {})
    logs = dict(evidence.get("logs") or {})
    lines.extend(["", "Build/runtime evidence:"])
    if build.get("summary"):
        lines.append(f"- Build: {build['summary']}")
    if runtime.get("summary"):
        lines.append(f"- Runtime: {runtime['summary']}")
    for line in build.get("error_lines") or []:
        lines.append(f"- build log: `{line[:180]}`")
    for line in runtime.get("runtime_lines") or []:
        lines.append(f"- runtime log: `{line[:180]}`")
    if not build.get("error_lines") and not runtime.get("runtime_lines") and logs.get("api_limited"):
        lines.append("- Vercel API returned limited log metadata; deeper logs may require browser fallback.")


def _append_domain_health(lines: list[str], evidence: dict[str, Any]) -> None:
    health = dict(evidence.get("domain_health") or {})
    lines.extend(["", "Domain health:"])
    if not health.get("ok"):
        lines.append(f"- Domain checks unavailable: {health.get('error') or 'unknown error'}")
        return
    lines.append(f"- Summary: {health.get('summary') or '—'}")
    for check in health.get("checks") or []:
        if not isinstance(check, dict):
            continue
        status = "reachable" if check.get("reachable") else "unreachable"
        code = check.get("status_code")
        suffix = f" (HTTP {code})" if code else ""
        lines.append(f"- `{check.get('domain')}` → **{status}**{suffix}")


def _append_env_metadata(lines: list[str], evidence: dict[str, Any]) -> None:
    env = dict(evidence.get("env_metadata") or {})
    if env.get("skipped"):
        return
    lines.extend(["", "Env metadata (keys/targets only):"])
    if not env.get("ok"):
        lines.append(f"- Env metadata unavailable: {env.get('error') or 'unknown error'}")
        return
    lines.append(f"- {env.get('env_count', 0)} configured variable(s)")
    for row in env.get("env_metadata") or []:
        if isinstance(row, dict) and row.get("key"):
            lines.append(f"- `{row['key']}` target={row.get('target') or '—'}")
    lines.append("- Secret values are never returned.")


def _compose_findings(evidence: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    failed = dict(evidence.get("failed_deployment") or {})
    build = dict(evidence.get("build_analysis") or {})
    runtime = dict(evidence.get("runtime_analysis") or {})
    health = dict(evidence.get("domain_health") or {})
    correlation = dict(evidence.get("github_correlation") or {})

    if failed:
        latest = dict(evidence.get("latest_deployment") or {})
        if (
            latest
            and failed.get("id") != latest.get("id")
            and str(latest.get("state") or "").lower() in {"ready", "completed"}
        ):
            findings.append(
                "Current production deployment is healthy; an older failed deployment remains in history."
            )
        else:
            findings.append(
                f"Latest failed deployment is `{failed.get('state')}` on branch `{failed.get('branch') or '—'}` — treat production as at risk until resolved."
            )
    elif build.get("error_lines"):
        findings.append("Build log excerpt contains error lines on the inspected deployment.")
    else:
        latest = dict(evidence.get("latest_deployment") or {})
        if str(latest.get("state") or "").lower() in {"ready", "completed"}:
            findings.append("Latest Vercel deployment state looks healthy on the API surface.")
        else:
            findings.append("Latest deployment state is not clearly healthy — inspect build/runtime evidence.")

    if runtime.get("runtime_lines"):
        findings.append("Runtime log excerpt shows errors that may explain post-deploy failures.")

    unreachable = [row for row in health.get("checks") or [] if isinstance(row, dict) and not row.get("reachable")]
    if unreachable:
        findings.append(f"{len(unreachable)} production domain(s) failed reachability checks.")

    github = dict(correlation.get("evidence") or {})
    workflow = dict(github.get("workflow_diagnostic") or {})
    if workflow.get("latest_failed_run"):
        findings.append("Linked GitHub workflow is failing — Vercel deploy likely consumed a bad commit or blocked CI.")

    if not findings:
        findings.append("Vercel evidence is inconclusive; fetch GitHub workflow logs if CI gates deploy.")
    return [f"- {item}" for item in findings]


def _next_readonly_step(evidence: dict[str, Any], *, operation: str) -> str:
    failed = dict(evidence.get("failed_deployment") or {})
    build = dict(evidence.get("build_analysis") or {})
    correlation = dict(evidence.get("github_correlation") or {})
    repo = str(dict(evidence.get("project", {}).get("details", {})).get("repo_link") or "")

    if failed or build.get("error_lines"):
        if repo:
            return f"Read the failing build step logs, then inspect GitHub workflow/check status for `{repo}` on commit `{failed.get('commit') or '—'}`."
        return "Read the failing build step logs, then compare the deployment commit against the latest green CI run."
    if correlation.get("available") is False and repo:
        return f"Add GitHub API access and inspect workflow/check status for `{repo}` on the deployed commit."
    if operation == "domains":
        return "Verify DNS/proxy settings for any unreachable production domain, then re-check deployment alias mapping."
    if operation == "env_metadata":
        return "Confirm required env keys exist for the production target without exposing secret values."
    return "If production is still unhealthy, inspect Railway/Vercel runtime logs for the currently serving deployment revision."
