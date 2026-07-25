# SPDX-License-Identifier: Apache-2.0
"""Resolve explicit provider/project targets before session memory wins."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

TargetSource = Literal["registry", "extracted", "path", "provider_mention", "readonly_intent"]

_EXPLICIT_PROVIDER_RX = re.compile(r"\b(railway|vercel|github|docker|kubernetes|aws|gcp|azure)\b", re.I)
_REPO_SLUG_RX = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b")
_VERCEL_PROJECT_NAME_RX = re.compile(r"\b(?:for|on|in)\s+([a-z0-9][a-z0-9._-]+)\b", re.I)
_DEPLOY_VERB_RX = re.compile(r"\b(?:deploye?|deploy(?:ment)?|redeploy)\b", re.I)
_DIAGNOSTIC_INTENT_RX = re.compile(
    r"\b(?:error|fail(?:ed|ure)?|fix|broken|check|investigate|diagnos(?:e|is)|health|logs?|status|report\s+back)\b",
    re.I,
)
_PROJECT_STOPWORDS = frozenset(
    {
        "vercel",
        "railway",
        "github",
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
        "any",
        "there",
        "health",
        "logs",
    }
)


@dataclass(frozen=True)
class ExplicitOperationalTarget:
    provider: str = ""
    project: str = ""
    service: str = ""
    environment: str = "production"
    repo: str = ""
    vercel_project: str = ""
    alias: str = ""
    target_id: str = ""
    source: TargetSource = "extracted"
    has_diagnostic_intent: bool = False
    has_deploy_intent: bool = False

    def path_label(self) -> str:
        if self.provider == "vercel" and self.vercel_project:
            return f"vercel / {self.vercel_project}"
        if self.provider == "github" and self.repo:
            return f"github / {self.repo}"
        if self.project and self.service:
            env = self.environment or "production"
            return f"{self.project} / {env} / {self.service}"
        if self.project:
            return self.project
        if self.vercel_project:
            return self.vercel_project
        if self.repo:
            return self.repo
        return self.alias or ""


def resolve_explicit_operational_target(text: str) -> ExplicitOperationalTarget | None:
    """Return the user's explicitly named operational target, if any."""
    raw = (text or "").strip()
    if not raw:
        return None

    diagnostic = bool(_DIAGNOSTIC_INTENT_RX.search(raw))
    deploy = bool(_DEPLOY_VERB_RX.search(raw))
    provider_mention = _explicit_provider(raw)
    repo = _extract_repo_slug(raw)
    vercel_project = _extract_project_hint(raw)
    path_target = _extract_path_target(raw)

    registry_row = _match_registry(raw, repo=repo)
    if registry_row is not None:
        return _target_from_registry(registry_row, text=raw, diagnostic=diagnostic, deploy=deploy)

    if path_target is not None:
        return path_target

    if provider_mention == "vercel" and (vercel_project or diagnostic or deploy):
        return ExplicitOperationalTarget(
            provider="vercel",
            vercel_project=vercel_project,
            project=vercel_project,
            source="provider_mention",
            has_diagnostic_intent=diagnostic,
            has_deploy_intent=deploy,
        )

    if provider_mention == "github" and (repo or diagnostic):
        return ExplicitOperationalTarget(
            provider="github",
            repo=repo,
            source="provider_mention",
            has_diagnostic_intent=diagnostic,
            has_deploy_intent=deploy,
        )

    if provider_mention == "railway" and diagnostic:
        return ExplicitOperationalTarget(
            provider="railway",
            source="provider_mention",
            has_diagnostic_intent=diagnostic,
            has_deploy_intent=deploy,
        )

    if vercel_project and diagnostic and re.search(r"\bvercel\b", raw, re.I):
        return ExplicitOperationalTarget(
            provider="vercel",
            vercel_project=vercel_project,
            project=vercel_project,
            source="extracted",
            has_diagnostic_intent=True,
            has_deploy_intent=deploy,
        )

    if repo and diagnostic:
        return ExplicitOperationalTarget(
            provider="github",
            repo=repo,
            source="extracted",
            has_diagnostic_intent=True,
            has_deploy_intent=deploy,
        )

    if provider_mention and (diagnostic or deploy):
        return ExplicitOperationalTarget(
            provider=provider_mention,
            source="provider_mention",
            has_diagnostic_intent=diagnostic,
            has_deploy_intent=deploy,
        )

    return None


def explicit_target_overrides_session_context(text: str, *, session_id: str = "default") -> bool:
    """True when the user named a target that must not inherit stale session/thread memory."""
    raw = (text or "").strip()
    if not raw:
        return False

    from aethos_core.operational_target_resolution.provider_intent_guard import (
        blocks_provider_readonly_diagnostics_route,
        primary_explicit_provider,
    )
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
        is_explicit_provider_readonly_request,
    )

    if blocks_provider_readonly_diagnostics_route(raw):
        return True

    if is_explicit_provider_readonly_request(raw):
        return True

    primary = primary_explicit_provider(raw)
    if primary:
        active = _active_session_target(session_id)
        if active is None or primary != active.provider:
            return True

    explicit = resolve_explicit_operational_target(raw)
    if explicit is not None and (explicit.has_diagnostic_intent or explicit.has_deploy_intent):
        active = _active_session_target(session_id)
        if active is None:
            return True
        return _targets_conflict(explicit, active)

    try:
        from aethos_core.providers.vercel.greenfield_deployment.greenfield_intent import (
            is_vercel_greenfield_deployment_intent,
        )

        if is_vercel_greenfield_deployment_intent(raw):
            return True
    except Exception:
        pass

    return False


def should_route_explicit_provider_diagnostics(text: str, *, session_id: str = "default") -> bool:
    """Route to provider readonly diagnostics before verification/thread follow-ups."""
    raw = (text or "").strip()
    if not raw:
        return False

    from aethos_core.operational_target_resolution.provider_intent_guard import (
        blocks_provider_readonly_diagnostics_route,
        is_valid_vercel_project_hint,
        primary_explicit_provider,
        requires_vercel_in_text_for_readonly,
    )
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
        classify_readonly_provider_intent,
        is_explicit_provider_readonly_request,
    )
    from aethos_core.runtime.vercel_readonly_jobs import infer_vercel_mutating_intent

    if blocks_provider_readonly_diagnostics_route(raw):
        return False

    if infer_vercel_mutating_intent(raw):
        return False

    primary = primary_explicit_provider(raw)
    if primary == "railway":
        return False

    if is_explicit_provider_readonly_request(raw):
        intent = classify_readonly_provider_intent(raw)
        if intent is None:
            return False
        if intent.provider == "github":
            return True
        if intent.provider == "vercel":
            if not requires_vercel_in_text_for_readonly(raw, project_hint=intent.project):
                return False
            if intent.project and not is_valid_vercel_project_hint(intent.project):
                return False
            if intent.operation != "projects":
                return True
            return bool(intent.project or intent.repo)
        return False

    explicit = resolve_explicit_operational_target(raw)
    if explicit is None or not explicit.has_diagnostic_intent:
        return False

    if explicit.provider == "vercel":
        if not requires_vercel_in_text_for_readonly(raw, project_hint=explicit.vercel_project):
            return False
        if explicit.vercel_project and not is_valid_vercel_project_hint(explicit.vercel_project):
            return False
        return True

    if explicit.provider == "github" and explicit.repo:
        return True

    return False


def request_overrides_stale_operational_thread(text: str, *, session_id: str = "default") -> bool:
    """Back-compat alias used across follow-up routers."""
    return explicit_target_overrides_session_context(text, session_id=session_id)


def _explicit_provider(text: str) -> str:
    match = _EXPLICIT_PROVIDER_RX.search(text or "")
    return match.group(1).lower() if match else ""


def _extract_repo_slug(text: str) -> str:
    match = _REPO_SLUG_RX.search(text or "")
    if not match:
        return ""
    slug = match.group(1).strip()
    if slug.lower() in {"can/you", "my/github"}:
        return ""
    return slug if "/" in slug else ""


def _extract_project_hint(text: str) -> str:
    raw = text or ""
    from aethos_core.operational_target_resolution.provider_intent_guard import is_valid_vercel_project_hint

    quoted = re.search(r"[`\"']([^`\"']+)[`\"']", raw)
    if quoted:
        candidate = quoted.group(1).strip()
        if is_valid_vercel_project_hint(candidate):
            return candidate
    match = re.search(r"\bproject\s+([A-Za-z0-9_.-]+)\b", raw, re.I)
    if match:
        candidate = match.group(1).strip()
        if is_valid_vercel_project_hint(candidate):
            return candidate
    deploy_match = re.search(r"\b(?:deploye?|deploy)\s+([a-z0-9][a-z0-9._-]+)\b", raw, re.I)
    if deploy_match:
        candidate = deploy_match.group(1).strip()
        if is_valid_vercel_project_hint(candidate):
            return candidate

    registry_row = _match_registry(raw, repo=_extract_repo_slug(raw))
    registry_aliases: set[str] = set()
    if registry_row:
        alias = str(registry_row.get("alias") or "").strip().lower()
        if alias:
            registry_aliases.add(alias)
        vercel_project = str(registry_row.get("vercel_project") or "").strip().lower()
        if vercel_project:
            registry_aliases.add(vercel_project)
        for item in registry_row.get("aliases") or []:
            token = str(item or "").strip().lower()
            if token:
                registry_aliases.add(token)

    if re.search(r"\bvercel\b", raw, re.I):
        for match in _VERCEL_PROJECT_NAME_RX.finditer(raw):
            candidate = match.group(1).strip()
            if is_valid_vercel_project_hint(candidate):
                return candidate

    if _DIAGNOSTIC_INTENT_RX.search(raw):
        for match in _VERCEL_PROJECT_NAME_RX.finditer(raw):
            candidate = match.group(1).strip()
            if is_valid_vercel_project_hint(candidate):
                return candidate

    lower = raw.lower()
    for alias in sorted(registry_aliases, key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", lower) and is_valid_vercel_project_hint(alias):
            return str(registry_row.get("vercel_project") or alias) if registry_row else alias

    return ""


def _extract_path_target(text: str) -> ExplicitOperationalTarget | None:
    try:
        from aethos_core.post_mutation_verification.verification_intent_router import extract_explicit_path_target
    except Exception:
        return None
    path = extract_explicit_path_target(text)
    if path is None:
        return None
    provider = str(getattr(path, "provider", "") or "railway").lower()
    return ExplicitOperationalTarget(
        provider=provider,
        project=str(getattr(path, "project", "") or ""),
        service=str(getattr(path, "service", "") or ""),
        environment=str(getattr(path, "environment", "") or "production"),
        source="path",
        has_diagnostic_intent=bool(_DIAGNOSTIC_INTENT_RX.search(text or "")),
        has_deploy_intent=bool(_DEPLOY_VERB_RX.search(text or "")),
    )


def _match_registry(text: str, *, repo: str) -> dict | None:
    from aethos_core.deployment_targets.registry import (
        find_target_by_repo,
        match_aliases_in_text,
    )

    row = match_aliases_in_text(text)
    if row is None and repo:
        row = find_target_by_repo(repo)
    return row


def _target_from_registry(row: dict, *, text: str, diagnostic: bool, deploy: bool) -> ExplicitOperationalTarget:
    alias = str(row.get("alias") or "")
    repo = str(row.get("repo") or "")
    vercel_project = str(row.get("vercel_project") or alias or "")
    railway_project = str(row.get("railway_project") or "")
    railway_service = str(row.get("railway_service") or "")
    default_provider = str(row.get("default_provider") or "").lower()

    if re.search(r"\brailway\b", text, re.I):
        provider = "railway"
    elif re.search(r"\bvercel\b", text, re.I):
        provider = "vercel"
    elif re.search(r"\bgithub\b", text, re.I):
        provider = "github"
    elif default_provider:
        provider = default_provider
    elif vercel_project and not (railway_project or railway_service):
        provider = "vercel"
    elif railway_project or railway_service:
        provider = "railway"
    elif repo:
        provider = "github"
    else:
        provider = ""

    service = railway_service
    resolved_vercel = vercel_project
    if provider == "railway":
        resolved_vercel = ""
        if not service and alias:
            service = alias
    elif provider == "vercel":
        service = ""

    return ExplicitOperationalTarget(
        provider=provider,
        alias=alias,
        target_id=str(row.get("target_id") or ""),
        repo=repo,
        vercel_project=resolved_vercel,
        project=railway_project or resolved_vercel or alias,
        service=service,
        environment=str(row.get("railway_environment") or "production"),
        source="registry",
        has_diagnostic_intent=diagnostic,
        has_deploy_intent=deploy,
    )


@dataclass(frozen=True)
class _SessionTarget:
    provider: str
    project: str
    service: str
    environment: str


def _active_session_target(session_id: str) -> _SessionTarget | None:
    from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

    thread = get_active_operational_thread(session_id)
    if thread is None:
        return None
    return _SessionTarget(
        provider=str(getattr(thread, "provider", "") or "railway").lower(),
        project=str(getattr(thread, "project", "") or "").lower(),
        service=str(getattr(thread, "service", "") or "").lower(),
        environment=str(getattr(thread, "environment", "") or "production").lower(),
    )


def _targets_conflict(explicit: ExplicitOperationalTarget, active: _SessionTarget) -> bool:
    if explicit.provider and active.provider and explicit.provider != active.provider:
        return True

    explicit_project = (explicit.vercel_project or explicit.project or explicit.alias).lower()
    if explicit_project and active.project and explicit_project != active.project:
        if explicit_project.replace("-", "") != active.project.replace("-", ""):
            return True

    explicit_service = (explicit.service or explicit.vercel_project or explicit.alias).lower()
    if explicit_service and active.service and explicit_service != active.service:
        if explicit_service.replace("-", "") != active.service.replace("-", ""):
            return True

    if explicit.repo:
        repo_base = explicit.repo.split("/")[-1].lower()
        if active.service and repo_base != active.service and repo_base != active.project:
            return True

    return bool(explicit.provider or explicit.vercel_project or explicit.repo)
