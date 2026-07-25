# SPDX-License-Identifier: Apache-2.0
"""Operational mutation intent detection — routes to preflight, not execution."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.operations.orchestration.job_taxonomy import CANONICAL_PREFLIGHT_JOB_TYPE

_RAILWAY_RX = re.compile(r"\brailway\b", re.I)
_RAILWAY_LOOSE_RX = re.compile(r"\brailwa(?:y)?\b", re.I)
_GITHUB_RX = re.compile(r"\b(github|actions|workflow)\b", re.I)
_GITHUB_WORKFLOW_RERUN_RX = re.compile(
    r"\brerun\b.*\b(latest\s+)?workflow\b|\bworkflow\b.*\brerun\b|\brerun\b.*\bactions\b",
    re.I,
)
_GITHUB_WORKFLOW_RUNS_RX = re.compile(
    r"\b(show|list|check|recent)\b.*\bworkflow\s+runs?\b|"
    r"\bworkflow\s+runs?\b.*\b(for|of|in)\b|"
    r"\b(show|list|check|recent)\b.*\bactions\s+runs?\b|"
    r"\bactions\s+runs?\b.*\b(for|of|in)\b",
    re.I,
)
_GITHUB_WORKFLOW_DIAGNOSTIC_RX = re.compile(
    r"\bwhy\b.*\b(workflow|action|build)s?\b.*\b(fail(?:ed|ure|s|ing)?|broke|broken|error(?:ed|s)?)\b|"
    r"\bwhy\b.*\b(fail(?:ed|ure|s|ing)?|broke|broken)\b.*\b(workflow|action|build)s?\b|"
    r"\bwhy\s+(?:is|are)\b.*\b(workflow|action|build)s?\b.*\b(fail(?:ing|ed|s)?|broken)\b|"
    r"\b(workflow|action|build)s?\s+(?:fail(?:ed|ure|s|ing)?|diagnostic)\b",
    re.I,
)
_GITHUB_WORKFLOW_JOBS_RX = re.compile(
    r"\b(show|list|check)\b.*\b(failed\s+)?(workflow|actions)\s+jobs?\b|"
    r"\b(show|list|check)\b.*\b(failed\s+)?(workflow|actions)\s+job\s+failures?\b|"
    r"\b(show|list|check)\b.*\bgithub\b.*\bfailed\s+jobs?\b|"
    r"\bworkflow\s+job\s+failures?\b|"
    r"\b(show|list|check)\b.*\b(?:github\s+)?workflow\s+logs?\b.*\b(for|of|on|in)\b",
    re.I,
)
_WHY_DID_REPO_WORKFLOW_FAIL_RX = re.compile(
    r"\bwhy\s+did\s+(?:the\s+)?([a-z0-9][a-z0-9._-]{1,62})\s+(?:workflow|action|build)\b",
    re.I,
)
_WHY_DID_WORKFLOW_FAIL_FOR_RX = re.compile(
    r"\bwhy\s+did\s+(?:the\s+)?(?:github\s+)?(?:workflow|action|build)\s+fail\s+(?:for|on|in)\s+([a-z0-9][a-z0-9._-]{1,62})\b",
    re.I,
)

_DEFERRED_CLOUD_RX = re.compile(
    r"\b(aws|amazon web services|gcp|google cloud|google-cloud|"
    r"cloudflare|render|supabase|azure)\b",
    re.I,
)

_VERCEL_REDEPLOY_RX = re.compile(
    r"\b(redeploy|re-?deploy)\b",
    re.I,
)
_VERCEL_RESTART_RX = re.compile(
    r"\b(restart|reboot)\b.*\b(app|application|service|project|deployment)?\b|"
    r"\brestart\b",
    re.I,
)
_VERCEL_STOP_RX = re.compile(
    r"\b(stop|shutdown|shut\s+down|kill|pause)\b.*\b(app|application|service|project|deployment)?\b|"
    r"\b(stop|kill)\b",
    re.I,
)
_VERCEL_LOGS_RX = re.compile(
    r"\b(check|show|view|get|tail|read)\b.*\b(logs?|logging)\b|"
    r"\blogs?\b.*\b(for|of|from)\b",
    re.I,
)
_VERCEL_DOWN_RX = re.compile(
    r"\b(why\s+is|why's|check\s+why)\b.*\b(down|failing|broken|unhealthy)\b|"
    r"\b(app|project|service)\b.*\b(down|failing|broken)\b|"
    r"\b(down|failing|broken)\b.*\b(app|project|service)\b",
    re.I,
)
_VERCEL_FAILURE_DIAGNOSTIC_RX = re.compile(
    r"\bwhy\s+did\b.*\b(fail(?:ed|ure|s)?|break(?:s|ing)?|broke|error(?:ed|s)?|crash(?:ed|es)?)\b|"
    r"\bwhy\s+(?:is|are)\b.*\b(fail(?:ing|ed|s)?|broken|breaking)\b|"
    r"\bwhat\s+failed\s+in\b|"
    r"\bwhy\s+(?:is|are)\b.*\bdeploy(?:ment)?s?\s+failing\b|"
    r"\bwhy\s+did\b.*\b(?:latest\s+)?deploy(?:ment)?s?\s+fail\b|"
    r"\bdeployment\s+fail(?:ed|ure)\b|"
    r"\b(fail(?:ed|ure|s)?|broken)\b.*\b(deploy(?:ment)?s?|build)\b",
    re.I,
)
_WHY_DID_TARGET_FAIL_RX = re.compile(
    r"\bwhy\s+did\s+([a-z0-9][a-z0-9._-]{1,62})\s+(?:fail(?:ed|s)?|break(?:s|ing)?|broke|error(?:ed|s)?|crash(?:ed|es)?)\b",
    re.I,
)
_WHY_IS_TARGET_FAILING_RX = re.compile(
    r"\bwhy\s+(?:is|are)\s+([a-z0-9][a-z0-9._-]{1,62})\s+(?:fail(?:ing|ed|s)?|broken|breaking|down)\b",
    re.I,
)
_WHAT_FAILED_IN_RX = re.compile(
    r"\bwhat\s+failed\s+in\s+([a-z0-9][a-z0-9._-]{1,62})\b",
    re.I,
)
_TARGET_HINT_SKIP = frozenset(
    {
        "vercel",
        "app",
        "service",
        "project",
        "deployment",
        "deploy",
        "deployments",
        "logs",
        "latest",
        "the",
        "it",
        "railway",
        "github",
        "workflow",
        "workflows",
        "runs",
        "actions",
        "repos",
        "repositories",
        "my",
        "build",
        "failure",
    }
)
_VERCEL_ENV_RX = re.compile(
    r"\b(set|add|update|change)\b.*\b(env|environment)\b|"
    r"\b(env\s*var|environment\s*variable)s?\b|"
    r"\bset\s+[A-Z][A-Z0-9_]+=[^\s]+",
    re.I,
)
_VERCEL_DEPLOY_GIT_RX = re.compile(
    r"\b(deploy)\b.*\b(from\s+)?(git|github|repo|branch)\b|"
    r"\bdeploy\s+from\s+git\b",
    re.I,
)
_VERCEL_DOMAINS_RX = re.compile(
    r"\b(show|list|check|which)\b.*\bdomains?\b|"
    r"\bdomains?\b.*\b(for|of|point\s+to)\b",
    re.I,
)
_VERCEL_DEPLOYMENTS_LIST_RX = re.compile(
    r"\b(show|check|list|recent)\b.*\bdeployments?\b|"
    r"\bdeployments?\b.*\b(for|of)\b",
    re.I,
)
_BROWSER_EVIDENCE_CAPTURE_RX = re.compile(
    r"\b(capture|take|show)\b.*\b(deployment\s+evidence|browser\s+evidence|screenshot)\b|"
    r"\b(deployment\s+evidence|browser\s+evidence)\b",
    re.I,
)
_VERCEL_PROJECT_DETAILS_RX = re.compile(
    r"\b(show|get|describe)\b.*\bproject\s+details?\b|"
    r"\bproject\s+details?\b.*\b(for|of)\b",
    re.I,
)

_VERCEL_INSPECTION_DEPLOY_RX = re.compile(
    r"\b(check|inspect)\b.*\b(failed\s+)?deployment\b|"
    r"\bdeployment\s+status\b",
    re.I,
)

_LOCAL_WORKSPACE_RX = re.compile(
    r"\b(check|inspect|fix)\b.*\b(local\s+)?(workspace|repo|code)\b|"
    r"\b(run\s+tests?|typecheck|lint)\b.*\b(local|repo|project)\b|"
    r"\b(commit|push)\b.*\b(changes?|repo)\b|"
    r"\bdeploy\s+this\s+repo\b|"
    r"\bfix\s+(the\s+)?(failing\s+)?app\b",
    re.I,
)

_QUOTED_TARGET_RX = re.compile(r"`([^`]+)`|'([^']+)'|\"([^\"]+)\"")
_FOR_TARGET_RX = re.compile(
    r"\bfor\s+([a-z0-9][a-z0-9._-]{1,62})\b",
    re.I,
)
_ON_PROVIDER_TARGET_RX = re.compile(
    r"\b([a-z0-9][a-z0-9._-]{1,62})\s+on\s+(?:railway|vercel|github)\b",
    re.I,
)
_MUTATION_TARGET_RX = re.compile(
    r"\b(?:restart|redeploy|re-?deploy|stop|start|kill|pause)\s+([a-z0-9][a-z0-9._-]{1,62})\b",
    re.I,
)


def _raw(text: str) -> str:
    return (text or "").strip()


def _add_hint(hints: list[str], seen: set[str], name: str) -> None:
    cleaned = (name or "").strip()
    if not cleaned:
        return
    low = cleaned.lower()
    if low in _TARGET_HINT_SKIP:
        return
    if low not in seen:
        seen.add(low)
        hints.append(cleaned)


def matches_vercel_failure_diagnostic(text: str) -> bool:
    raw = _raw(text)
    return bool(_VERCEL_DOWN_RX.search(raw) or _VERCEL_FAILURE_DIAGNOSTIC_RX.search(raw))


def extract_target_hints(text: str) -> list[str]:
    """Candidate project names from user message."""
    raw = _raw(text)
    hints: list[str] = []
    seen: set[str] = set()
    from aethos_core.providers.railway.target_resolver import extract_railway_service_phrase

    railway_phrase = extract_railway_service_phrase(raw)
    if railway_phrase:
        _add_hint(hints, seen, railway_phrase)
    for m in _QUOTED_TARGET_RX.finditer(raw):
        for g in m.groups():
            if g:
                _add_hint(hints, seen, g)
    for m in _FOR_TARGET_RX.finditer(raw):
        _add_hint(hints, seen, m.group(1))
    for m in _ON_PROVIDER_TARGET_RX.finditer(raw):
        _add_hint(hints, seen, m.group(1))
    for m in _MUTATION_TARGET_RX.finditer(raw):
        _add_hint(hints, seen, m.group(1))
    for rx in (_WHY_DID_TARGET_FAIL_RX, _WHY_IS_TARGET_FAILING_RX, _WHAT_FAILED_IN_RX):
        for m in rx.finditer(raw):
            _add_hint(hints, seen, m.group(1))
    for rx in (_WHY_DID_REPO_WORKFLOW_FAIL_RX, _WHY_DID_WORKFLOW_FAIL_FOR_RX):
        for m in rx.finditer(raw):
            _add_hint(hints, seen, m.group(1))
    return hints


def _cloud_operation_preflight(
    title: str,
    *,
    provider: str,
    operation_type: str,
    raw: str,
    hints: list[str],
) -> tuple[str, str, dict[str, Any]]:
    return (
        title,
        CANONICAL_PREFLIGHT_JOB_TYPE,
        {
            "user_request": raw,
            "provider": provider,
            "operation_type": operation_type,
            "target_hints": hints,
        },
    )


def _why_down_preflight(raw: str, hints: list[str]) -> tuple[str, str, dict[str, Any]]:
    return _cloud_operation_preflight(
        "Vercel down diagnostic preflight",
        provider="vercel",
        operation_type="why_down",
        raw=raw,
        hints=hints,
    )


def _railway_why_down_preflight(raw: str, hints: list[str]) -> tuple[str, str, dict[str, Any]]:
    return _cloud_operation_preflight(
        "Railway down diagnostic preflight",
        provider="railway",
        operation_type="why_down",
        raw=raw,
        hints=hints,
    )


def _github_workflow_jobs_preflight(
    raw: str, hints: list[str]
) -> tuple[str, str, dict[str, Any]] | None:
    if not _GITHUB_WORKFLOW_JOBS_RX.search(raw):
        return None
    return _cloud_operation_preflight(
        "GitHub workflow jobs preflight",
        provider="github",
        operation_type="workflow_jobs",
        raw=raw,
        hints=hints,
    )


def _github_workflow_diagnostic_preflight(
    raw: str, hints: list[str]
) -> tuple[str, str, dict[str, Any]] | None:
    if not _GITHUB_WORKFLOW_DIAGNOSTIC_RX.search(raw):
        return None
    return _cloud_operation_preflight(
        "GitHub workflow diagnostic preflight",
        provider="github",
        operation_type="workflow_diagnostic",
        raw=raw,
        hints=hints,
    )


def _infer_github_operation_preflight_intent(
    raw: str, hints: list[str]
) -> tuple[str, str, dict[str, Any]] | None:
    diagnostic = _github_workflow_diagnostic_preflight(raw, hints)
    if diagnostic:
        return diagnostic
    jobs = _github_workflow_jobs_preflight(raw, hints)
    if jobs:
        return jobs
    if _GITHUB_WORKFLOW_RUNS_RX.search(raw):
        return _cloud_operation_preflight(
            "GitHub workflow runs preflight",
            provider="github",
            operation_type="workflow_runs",
            raw=raw,
            hints=hints,
        )
    return None


def _infer_railway_operation_preflight_intent(
    raw: str, hints: list[str]
) -> tuple[str, str, dict[str, Any]] | None:
    if _VERCEL_ENV_RX.search(raw):
        return _cloud_operation_preflight(
            "Railway environment variable preflight",
            provider="railway",
            operation_type="set_env_var",
            raw=raw,
            hints=hints,
        )
    if _VERCEL_LOGS_RX.search(raw):
        return _cloud_operation_preflight(
            "Railway logs preflight",
            provider="railway",
            operation_type="check_logs",
            raw=raw,
            hints=hints,
        )
    if matches_vercel_failure_diagnostic(raw):
        return _railway_why_down_preflight(raw, hints)
    if _VERCEL_DEPLOYMENTS_LIST_RX.search(raw) and not _VERCEL_REDEPLOY_RX.search(raw):
        return _cloud_operation_preflight(
            "Railway deployments preflight",
            provider="railway",
            operation_type="list_deployments",
            raw=raw,
            hints=hints,
        )
    if _VERCEL_PROJECT_DETAILS_RX.search(raw):
        return _cloud_operation_preflight(
            "Railway project details preflight",
            provider="railway",
            operation_type="project_details",
            raw=raw,
            hints=hints,
        )
    if _VERCEL_INSPECTION_DEPLOY_RX.search(raw) and not _VERCEL_REDEPLOY_RX.search(raw):
        return _cloud_operation_preflight(
            "Railway deployment inspection preflight",
            provider="railway",
            operation_type="inspect_failed_deployment",
            raw=raw,
            hints=hints,
        )
    if _VERCEL_REDEPLOY_RX.search(raw):
        return _cloud_operation_preflight(
            "Railway redeploy preflight",
            provider="railway",
            operation_type="redeploy",
            raw=raw,
            hints=hints,
        )
    if _VERCEL_STOP_RX.search(raw):
        return _cloud_operation_preflight(
            "Railway stop preflight",
            provider="railway",
            operation_type="stop",
            raw=raw,
            hints=hints,
        )
    if _VERCEL_RESTART_RX.search(raw):
        return _cloud_operation_preflight(
            "Railway restart preflight",
            provider="railway",
            operation_type="restart",
            raw=raw,
            hints=hints,
        )
    return None


def infer_deferred_cloud_intent(text: str) -> str | None:
    m = _DEFERRED_CLOUD_RX.search(_raw(text))
    return m.group(1).lower() if m else None


def infer_operation_preflight_intent(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, Any]] | None:
    """
    Return (title, job_type, params) for a read-only preflight job, or None.
    Cloud providers use canonical operation_preflight with provider/operation metadata.
    """
    from aethos_core.chat.front_door_intent import is_canvas_render_request
    from aethos_core.chat.operational_master_router import master_router_has_priority_route
    from aethos_core.chat.route_trace import is_internal_diagnostics_query

    # A canvas render ("render/draw … on the canvas") must never be mistaken for a cloud
    # provider operation. The verb "render" also names a provider (render.com), which would
    # otherwise spin up a useless browser-diagnostics preflight with nothing to approve.
    if is_canvas_render_request(text):
        return None

    if is_internal_diagnostics_query(text):
        return None

    if master_router_has_priority_route(text, session_id=session_id):
        return None

    raw = _raw(text)
    if not raw:
        return None

    from aethos_core.chat.informational_turn_classifier import should_block_mutation_routing

    if should_block_mutation_routing(raw, session_id=session_id):
        return None

    from aethos_core.failed_service_investigation.global_preemption import is_cognition_owned_failure_investigation

    if is_cognition_owned_failure_investigation(text, session_id=session_id):
        return None

    if matches_vercel_failure_diagnostic(raw) and not re.search(r"\bvercel\b", raw, re.I):
        return None

    deferred = infer_deferred_cloud_intent(raw)
    if deferred:
        return (
            f"{deferred.title()} operation preflight (planned)",
            "operation_preflight",
            {
                "user_request": raw,
                "provider": deferred,
                "operation_type": "cloud_provider_planned",
                "target_hints": extract_target_hints(raw),
            },
        )

    hints = extract_target_hints(raw)

    if _RAILWAY_RX.search(raw) or _RAILWAY_LOOSE_RX.search(raw):
        railway = _infer_railway_operation_preflight_intent(raw, hints)
        if railway:
            return railway

    if hints and not (_GITHUB_RX.search(raw) or re.search(r"\bvercel\b", raw, re.I)):
        from aethos_core.operations.orchestration.provider_inference import infer_provider_for_hints

        inferred = infer_provider_for_hints(hints)
        if inferred.get("status") == "resolved" and inferred.get("provider") == "railway":
            railway = _infer_railway_operation_preflight_intent(raw, hints)
            if railway:
                return railway
        if inferred.get("status") == "ambiguous":
            names = ", ".join(
                f"{m.get('provider')}: {m.get('name')}" for m in (inferred.get("matches") or [])[:4]
            )
            return (
                "Provider ambiguity preflight",
                CANONICAL_PREFLIGHT_JOB_TYPE,
                {
                    "user_request": raw,
                    "provider": "unknown",
                    "operation_type": "provider_ambiguity",
                    "target_hints": hints,
                    "provider_inference": inferred,
                    "preflight_status": "needs_information",
                    "detail": f"I found this target in multiple providers: {names}. Which one should I use?",
                },
            )

    if _GITHUB_WORKFLOW_RERUN_RX.search(raw):
        return _cloud_operation_preflight(
            "GitHub workflow rerun preflight",
            provider="github",
            operation_type="workflow_rerun",
            raw=raw,
            hints=hints,
        )

    github_diagnostic = _github_workflow_diagnostic_preflight(raw, hints)
    if github_diagnostic:
        return github_diagnostic

    github_jobs = _github_workflow_jobs_preflight(raw, hints)
    if github_jobs:
        return github_jobs

    if _GITHUB_RX.search(raw):
        github = _infer_github_operation_preflight_intent(raw, hints)
        if github:
            return github

    from aethos_core.production.deployment_mode import is_hosted_deployment
    from aethos_core.providers.github.operations.repo_remote_read_api import (
        is_github_remote_repo_analysis_request,
    )

    if is_github_remote_repo_analysis_request(raw) or (
        is_hosted_deployment() and _LOCAL_WORKSPACE_RX.search(raw) and not re.search(r"\bvercel\b", raw, re.I)
    ):
        return _cloud_operation_preflight(
            "GitHub repository analysis preflight",
            provider="github",
            operation_type="remote_repo_analysis",
            raw=raw,
            hints=hints,
        )

    if _LOCAL_WORKSPACE_RX.search(raw) and not re.search(r"\bvercel\b", raw, re.I):
        if is_hosted_deployment():
            return None
        op = "local_workspace_fix"
        if re.search(r"\bcommit\b", raw, re.I):
            op = "local_commit_preflight"
        elif re.search(r"\bpush\b", raw, re.I):
            op = "local_push_preflight"
        elif re.search(r"\bdeploy\b", raw, re.I):
            op = "git_deploy_preflight"
        return (
            "Local workspace operation preflight",
            "local_workspace_fix_preflight",
            {"user_request": raw, "provider": "local", "operation_type": op, "target_hints": hints},
        )

    if _VERCEL_ENV_RX.search(raw):
        return _cloud_operation_preflight(
            "Vercel environment variable preflight",
            provider="vercel",
            operation_type="set_env_var",
            raw=raw,
            hints=hints,
        )

    if _VERCEL_LOGS_RX.search(raw):
        return _cloud_operation_preflight(
            "Vercel logs preflight",
            provider="vercel",
            operation_type="check_logs",
            raw=raw,
            hints=hints,
        )

    if matches_vercel_failure_diagnostic(raw):
        if is_cognition_owned_failure_investigation(text, session_id=session_id):
            return None
        return _why_down_preflight(raw, hints)

    if _VERCEL_DOMAINS_RX.search(raw) and not _VERCEL_ENV_RX.search(raw):
        return _cloud_operation_preflight(
            "Vercel domains preflight",
            provider="vercel",
            operation_type="list_domains",
            raw=raw,
            hints=hints,
        )

    if _VERCEL_DEPLOYMENTS_LIST_RX.search(raw) and not _VERCEL_REDEPLOY_RX.search(raw):
        if _BROWSER_EVIDENCE_CAPTURE_RX.search(raw):
            return None
        from aethos_core.operations.orchestration.provider_inference import infer_provider_for_hints

        inferred = infer_provider_for_hints(hints)
        if inferred.get("status") == "resolved" and inferred.get("provider") == "railway":
            return _cloud_operation_preflight(
                "Railway deployments preflight",
                provider="railway",
                operation_type="list_deployments",
                raw=raw,
                hints=hints,
            )
        # No explicit "vercel" — don't blindly default to a Vercel preflight (that mislabels
        # Railway services like aethos-api and forces an approval for a read-only check). Defer to
        # the agent runtime, which checks both Railway and Vercel inventories and answers a
        # read-only status directly.
        if not re.search(r"\bvercel\b", raw, re.I):
            return None
        return _cloud_operation_preflight(
            "Vercel deployments preflight",
            provider="vercel",
            operation_type="list_deployments",
            raw=raw,
            hints=hints,
        )

    if _VERCEL_PROJECT_DETAILS_RX.search(raw):
        return _cloud_operation_preflight(
            "Vercel project details preflight",
            provider="vercel",
            operation_type="project_details",
            raw=raw,
            hints=hints,
        )

    if _VERCEL_INSPECTION_DEPLOY_RX.search(raw) and not _VERCEL_REDEPLOY_RX.search(raw):
        return _cloud_operation_preflight(
            "Vercel deployment inspection preflight",
            provider="vercel",
            operation_type="inspect_failed_deployment",
            raw=raw,
            hints=hints,
        )

    if _VERCEL_REDEPLOY_RX.search(raw):
        return _cloud_operation_preflight(
            "Vercel redeploy preflight",
            provider="vercel",
            operation_type="redeploy",
            raw=raw,
            hints=hints,
        )

    if _VERCEL_STOP_RX.search(raw):
        return _cloud_operation_preflight(
            "Vercel stop preflight",
            provider="vercel",
            operation_type="stop",
            raw=raw,
            hints=hints,
        )

    if _VERCEL_RESTART_RX.search(raw):
        if re.search(r"\brestart\b.*\baethos\b|\baethos\b.*\brestart\b", raw, re.I):
            return None
        if _RAILWAY_LOOSE_RX.search(raw):
            return _cloud_operation_preflight(
                "Railway restart preflight",
                provider="railway",
                operation_type="restart",
                raw=raw,
                hints=hints,
            )
        return _cloud_operation_preflight(
            "Vercel restart preflight",
            provider="vercel",
            operation_type="restart",
            raw=raw,
            hints=hints,
        )

    if _VERCEL_DEPLOY_GIT_RX.search(raw):
        # Honor an explicit Railway target (mirror the restart branch above);
        # only fall back to Vercel when no provider is named.
        if _RAILWAY_LOOSE_RX.search(raw):
            return _cloud_operation_preflight(
                "Railway deploy from Git preflight",
                provider="railway",
                operation_type="deploy_from_git",
                raw=raw,
                hints=hints,
            )
        return _cloud_operation_preflight(
            "Vercel deploy from Git preflight",
            provider="vercel",
            operation_type="deploy_from_git",
            raw=raw,
            hints=hints,
        )

    return None
