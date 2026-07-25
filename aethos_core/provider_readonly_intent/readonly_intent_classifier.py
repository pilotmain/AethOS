# SPDX-License-Identifier: Apache-2.0
"""Explicit GitHub/Vercel readonly intent classification."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

ReadonlyProvider = Literal["github", "vercel"]
GithubReadonlyOperation = Literal[
    "repo_status",
    "recent_commits",
    "workflows",
    "failed_checks",
    "workflow_logs",
    "workflow_failures",
    "branch_divergence",
    "pr_status",
    "releases",
    "live_diagnosis",
    "repo_inventory",
]
VercelReadonlyOperation = Literal[
    "deployments",
    "projects",
    "logs",
    "domains",
    "env_metadata",
    "live_diagnosis",
    "failed_deployment",
]

_GITHUB_RX = re.compile(r"\bgithub\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)
_REPO_SLUG_RX = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b")

_GITHUB_READONLY_RX = re.compile(
    r"\b("
    r"inspect\b.*\b(?:github\b.*\b)?(?:repo|repository|repositories|workflow|workflows|checks?|commits?|branch|status)"
    r"|(?:repo|repository)\b.*\b(?:status|branch|commits?|workflows?|checks?)"
    r"|(?:check|show|inspect|read|list)\b.*\b(?:github\b.*\b)?(?:repo|repository|workflows?|commits?|checks?|workflow\s+logs?)"
    r"|(?:recent|latest)\s+commits?"
    r"|failed\s+checks?"
    r"|workflow\s+(?:runs?|logs?|status|failures?)"
    r"|(?:failing|failed)\s+(?:ci|workflow|github\s+actions?)"
    r"|branch\s+(?:divergence|behind|ahead)"
    r"|pull\s+requests?"
    r"|(?:pr|pull\s+request)\s+status"
    r"|(?:release|tag)s?"
    r"|diagnos(?:e|is)\b.*\bgithub\b"
    r"|show\b.*\bgithub\b.*\b(?:repos?|repositories)"
    r")\b",
    re.I,
)

_VERCEL_READONLY_RX = re.compile(
    r"\b("
    r"inspect\b.*\bvercel\b.*\b(?:deployments?|projects?|logs?|domains?|env(?:ironment)?\s+(?:var|metadata))"
    r"|(?:check|show|inspect|list|read)\b.*\bvercel\b.*\b(?:deployments?|projects?|apps?|services?|logs?|domains?|env)"
    r"|vercel\b.*\b(?:deployments?|projects?|apps?|services?|logs?|domains?)\b.*\b(?:inspect|show|check|list)"
    r"|show\b.*\bvercel\b.*\b(?:projects?|apps?|deployments?)"
    r"|vercel\b.*\benv(?:ironment)?\s+(?:var|metadata)"
    r"|(?:diagnos(?:e|is)|investigate|live\s+diagnostics?)\b.*\bvercel\b"
    r"|vercel\b.*\b(?:diagnos(?:e|is)|investigate|live\s+diagnostics?)\b"
    r"|(?:why\s+did|why\s+is)\b.*\bvercel\b.*\b(?:deployment|deploy|build)\b.*\bfail"
    r"|(?:failing|failed)\b.*\bvercel\b.*\b(?:deployment|deploy|build)\b"
    r")\b",
    re.I,
)

_GITHUB_REPO_STATUS_RX = re.compile(r"\b(repo(?:sitory)?\s+status|branch\s+status|inspect\b.*\bstatus)\b", re.I)
_GITHUB_COMMITS_RX = re.compile(r"\b(recent|latest)\s+commits?\b|\bshow\s+commits?\b", re.I)
_GITHUB_WORKFLOWS_RX = re.compile(r"\bworkflows?\b|\bworkflow\s+runs?\b", re.I)
_GITHUB_CHECKS_RX = re.compile(r"\bfailed\s+checks?\b|\bcheck\s+runs?\b", re.I)
_GITHUB_LOGS_RX = re.compile(r"\bworkflow\s+logs?\b|\bread\s+workflow\s+logs?\b", re.I)
_GITHUB_WORKFLOW_FAILURES_RX = re.compile(
    r"\b(?:failing|failed)\s+(?:ci|workflow|github\s+actions?)\b|\bworkflow\s+failures?\b|\bwhy\s+did\b.*\b(?:workflow|ci|build)\b.*\bfail",
    re.I,
)
_GITHUB_BRANCH_DIVERGENCE_RX = re.compile(
    r"\bbranch\s+(?:divergence|behind|ahead)\b|\b(?:ahead|behind)\b.*\b(?:branch|commits?)\b",
    re.I,
)
_GITHUB_PR_RX = re.compile(r"\b(?:pull\s+requests?|pr\s+status)\b", re.I)
_GITHUB_RELEASES_RX = re.compile(r"\b(?:release|tag)s?\b", re.I)
_GITHUB_LIVE_DIAGNOSIS_RX = re.compile(
    r"\b(?:diagnos(?:e|is)|investigate|live\s+diagnostics?)\b.*\bgithub\b|\bgithub\b.*\b(?:diagnos(?:e|is)|investigate|live\s+diagnostics?)\b",
    re.I,
)
_GITHUB_INVENTORY_RX = re.compile(r"\b(show|list)\b.*\b(?:my\s+)?(?:github\s+)?repos?\b", re.I)

_VERCEL_DEPLOYMENTS_RX = re.compile(r"\b(deployments?)\b", re.I)
_VERCEL_PROJECTS_RX = re.compile(r"\b(projects?|apps?|services?)\b", re.I)
_VERCEL_LOGS_RX = re.compile(r"\b(logs?|build\s+logs?|runtime\s+logs?)\b", re.I)
_VERCEL_DOMAINS_RX = re.compile(r"\bdomains?\b", re.I)
_VERCEL_ENV_RX = re.compile(r"\benv(?:ironment)?\s+(?:var(?:s)?|metadata)\b", re.I)
_VERCEL_LIVE_DIAGNOSIS_RX = re.compile(
    r"\b(?:diagnos(?:e|is)|investigate|live\s+diagnostics?)\b.*\bvercel\b|\bvercel\b.*\b(?:diagnos(?:e|is)|investigate|live\s+diagnostics?)\b",
    re.I,
)
_VERCEL_FAILED_DEPLOY_RX = re.compile(
    r"\b(?:why\s+did|why\s+is)\b.*\bvercel\b.*\b(?:deployment|deploy|build)\b.*\bfail"
    r"|\b(?:failing|failed)\b.*\bvercel\b.*\b(?:deployment|deploy|build)\b"
    r"|\bvercel\b.*\b(?:failing|failed)\b.*\b(?:deployment|deploy|build)\b",
    re.I,
)
_VERCEL_ERROR_CHECK_RX = re.compile(
    r"\bvercel\b.*\b(?:error|fix|fail(?:ed|ure)?)\b"
    r"|\b(?:check|fix|investigate)\b.*\b(?:error|fail(?:ed|ure)?)\b.*\bvercel\b"
    r"|\b(?:error|fail(?:ed|ure)?)\b.*\bvercel\b"
    r"|\bvercel\b.*\b(?:for\s+)?[a-z0-9][a-z0-9._-]+\b",
    re.I,
)
_VERCEL_PROJECT_NAME_RX = re.compile(r"\b(?:for|on|in)\s+([a-z0-9][a-z0-9._-]+)\b", re.I)
_VERCEL_PROJECT_STOPWORDS = frozenset(
    {
        "vercel",
        "deployment",
        "deployments",
        "deploy",
        "deploye",
        "error",
        "errors",
        "fix",
        "the",
        "and",
        "report",
        "back",
        "anything",
        "needed",
        "remote",
        "repo",
        "from",
    }
)
_OPS_INTENT_RX = re.compile(
    r"\b(?:error|fail(?:ed|ure)?|fix|broken|check|investigate|diagnos(?:e|is))\b",
    re.I,
)
_DEPLOY_VERB_RX = re.compile(r"\b(?:deploye?|deploy(?:ment)?|redeploy)\b", re.I)


@dataclass(frozen=True)
class ReadonlyProviderIntent:
    provider: ReadonlyProvider
    operation: str
    repo: str = ""
    project: str = ""


def mentions_explicit_readonly_provider(text: str) -> ReadonlyProvider | None:
    raw = (text or "").strip()
    if not raw:
        return None
    from aethos_core.providers.github.mutations.rerun_intent_continuation import is_github_workflow_rerun_request

    if is_github_workflow_rerun_request(raw):
        return None
    has_github = bool(_GITHUB_RX.search(raw))
    has_vercel = bool(_VERCEL_RX.search(raw))
    if has_github and _GITHUB_READONLY_RX.search(raw):
        return "github"
    if has_vercel and (_VERCEL_READONLY_RX.search(raw) or _VERCEL_ERROR_CHECK_RX.search(raw)):
        return "vercel"
    if _known_vercel_project_ops_intent(raw):
        return "vercel"
    if has_github and re.search(r"\b(repo|repository|workflow|commit|checks?)\b", raw, re.I):
        return "github"
    return None


def is_explicit_provider_readonly_request(text: str) -> bool:
    return mentions_explicit_readonly_provider(text) is not None


def _registry_backed_vercel_ops_intent(text: str) -> bool:
    from aethos_core.operational_target_resolution.explicit_target_resolver import (
        resolve_explicit_operational_target,
    )
    from aethos_core.operational_target_resolution.provider_intent_guard import (
        blocks_provider_readonly_diagnostics_route,
        is_valid_vercel_project_hint,
        requires_vercel_in_text_for_readonly,
    )

    if blocks_provider_readonly_diagnostics_route(text):
        return False
    explicit = resolve_explicit_operational_target(text)
    if explicit is None or not explicit.has_diagnostic_intent:
        return False
    if explicit.provider != "vercel" and not explicit.vercel_project:
        return False
    if explicit.vercel_project and not is_valid_vercel_project_hint(explicit.vercel_project):
        return False
    return requires_vercel_in_text_for_readonly(text, project_hint=explicit.vercel_project)


def _known_vercel_project_ops_intent(text: str) -> bool:
    return _registry_backed_vercel_ops_intent(text)


def request_overrides_stale_operational_thread(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.operational_target_resolution.explicit_target_resolver import (
        explicit_target_overrides_session_context,
    )

    return explicit_target_overrides_session_context(text, session_id=session_id)


def should_yield_active_thread_for_readonly(text: str, *, session_id: str = "default") -> bool:
    return request_overrides_stale_operational_thread(text, session_id=session_id)


def extract_github_repo_slug(text: str) -> str:
    match = _REPO_SLUG_RX.search(text or "")
    if match:
        slug = match.group(1).strip()
        if slug.lower() not in {"can/you", "my/github"} and "/" in slug:
            return slug
    return ""


def extract_vercel_project_hint(text: str) -> str:
    from aethos_core.operational_target_resolution.explicit_target_resolver import _extract_project_hint

    return _extract_project_hint(text)


def classify_github_readonly_intent(text: str) -> ReadonlyProviderIntent | None:
    from aethos_core.providers.github.mutations.rerun_intent_continuation import is_github_workflow_rerun_request

    if is_github_workflow_rerun_request(text):
        return None
    if mentions_explicit_readonly_provider(text) != "github":
        return None
    raw = text or ""
    if _GITHUB_INVENTORY_RX.search(raw):
        operation: GithubReadonlyOperation = "repo_inventory"
    elif _GITHUB_LIVE_DIAGNOSIS_RX.search(raw):
        operation = "live_diagnosis"
    elif _GITHUB_LOGS_RX.search(raw):
        operation = "workflow_logs"
    elif _GITHUB_WORKFLOW_FAILURES_RX.search(raw):
        operation = "workflow_failures"
    elif _GITHUB_CHECKS_RX.search(raw):
        operation = "failed_checks"
    elif _GITHUB_PR_RX.search(raw):
        operation = "pr_status"
    elif _GITHUB_RELEASES_RX.search(raw):
        operation = "releases"
    elif _GITHUB_BRANCH_DIVERGENCE_RX.search(raw):
        operation = "branch_divergence"
    elif _GITHUB_COMMITS_RX.search(raw):
        operation = "recent_commits"
    elif _GITHUB_WORKFLOWS_RX.search(raw):
        operation = "workflows"
    elif _GITHUB_REPO_STATUS_RX.search(raw) or re.search(r"\bstatus\b", raw, re.I):
        operation = "repo_status"
    else:
        operation = "live_diagnosis"
    return ReadonlyProviderIntent(provider="github", operation=operation, repo=extract_github_repo_slug(raw))


def classify_vercel_readonly_intent(text: str) -> ReadonlyProviderIntent | None:
    from aethos_core.operational_target_resolution.provider_intent_guard import (
        blocks_provider_readonly_diagnostics_route,
        is_valid_vercel_project_hint,
        requires_vercel_in_text_for_readonly,
    )

    if blocks_provider_readonly_diagnostics_route(text):
        return None
    if mentions_explicit_readonly_provider(text) != "vercel":
        return None
    raw = text or ""
    project = extract_vercel_project_hint(raw)
    if not requires_vercel_in_text_for_readonly(raw, project_hint=project):
        return None
    if project and not is_valid_vercel_project_hint(project):
        project = ""
    if _VERCEL_LIVE_DIAGNOSIS_RX.search(raw):
        operation: VercelReadonlyOperation = "live_diagnosis"
    elif _VERCEL_FAILED_DEPLOY_RX.search(raw) or (
        _VERCEL_ERROR_CHECK_RX.search(raw) and re.search(r"\b(?:error|fail|fix)\b", raw, re.I)
    ):
        operation = "failed_deployment"
    elif _VERCEL_ENV_RX.search(raw):
        operation = "env_metadata"
    elif _VERCEL_DOMAINS_RX.search(raw):
        operation = "domains"
    elif _VERCEL_LOGS_RX.search(raw) or re.search(r"\berror\s+logs?\b", raw, re.I):
        operation = "logs"
    elif _VERCEL_PROJECTS_RX.search(raw) or re.search(
        r"\b(list|show|all|every)\b.*\bprojects?\b", raw, re.I
    ):
        operation = "projects"
    elif re.search(r"\bhealth\b", raw, re.I) and extract_vercel_project_hint(raw):
        operation = "live_diagnosis"
    elif _VERCEL_DEPLOYMENTS_RX.search(raw):
        operation = "deployments"
    else:
        operation = "deployments"
    return ReadonlyProviderIntent(
        provider="vercel",
        operation=operation,
        project=extract_vercel_project_hint(raw),
    )


def classify_readonly_provider_intent(text: str) -> ReadonlyProviderIntent | None:
    github = classify_github_readonly_intent(text)
    if github is not None:
        return github
    return classify_vercel_readonly_intent(text)
