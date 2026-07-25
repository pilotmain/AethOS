# SPDX-License-Identifier: Apache-2.0
"""AETHOS_SOLO_PRODUCTION_EXECUTION_MODE — local trusted developer fast path."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    RailwayExecutionEnablementPolicy,
    is_production_environment,
)

_DESTRUCTIVE_RX = re.compile(
    r"\b(?:delete|destroy|drop\s+(?:database|db|schema|table)|reset\s+database|wipe\s+data)\b",
    re.I,
)


@dataclass(frozen=True)
class SoloExecutionConfig:
    enabled: bool
    provider_scope: str
    allowed_repos: tuple[str, ...]
    allowed_providers: tuple[str, ...]
    allowed_environments: tuple[str, ...]
    allow_production: bool
    require_final_confirmation: bool


@dataclass
class SoloEligibilityResult:
    ok: bool
    blocker_code: str = ""
    detail: str = ""
    required_action: str = ""
    safe_next_command: str = ""
    missing_env_names: list[str] = field(default_factory=list)


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip().lower() for item in (value or "").split(",") if item.strip())


def load_solo_execution_config() -> SoloExecutionConfig:
    settings = get_settings()
    scope_raw = str(settings.aethos_solo_execution_provider or "").strip().lower()
    provider_scope = scope_raw if scope_raw and "," not in scope_raw else ""
    return SoloExecutionConfig(
        enabled=bool(settings.aethos_solo_execution_mode),
        provider_scope=provider_scope,
        allowed_repos=_parse_csv(settings.aethos_solo_allowed_repos),
        allowed_providers=_parse_csv(settings.aethos_solo_allowed_providers),
        allowed_environments=_parse_csv(settings.aethos_solo_allowed_environments),
        allow_production=bool(settings.aethos_solo_allow_production),
        require_final_confirmation=bool(settings.aethos_solo_require_final_confirmation),
    )


def is_solo_execution_mode_enabled() -> bool:
    cfg = load_solo_execution_config()
    if not cfg.enabled:
        return False
    settings = get_settings()
    if str(settings.app_env or "").strip().lower() in {"production", "prod"}:
        return False
    return True


_GITHUB_HTTPS_RX = re.compile(r"github\.com[:/]+([^/\s]+)/([^/\s#?]+)", re.I)
_GITHUB_SSH_RX = re.compile(r"git@github\.com:([^/\s]+)/([^/\s#?]+)", re.I)


def _normalize_repo_slug(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    for rx in (_GITHUB_SSH_RX, _GITHUB_HTTPS_RX):
        match = rx.search(raw)
        if match:
            repo = match.group(2).lower().removesuffix(".git")
            return f"{match.group(1).lower()}/{repo}"
    cleaned = raw.lower().removesuffix(".git")
    if "/" in cleaned and "@" not in cleaned and "://" not in cleaned:
        return cleaned
    return cleaned


def validate_solo_greenfield_eligibility(
    *,
    plan: dict[str, Any],
    env_report: dict[str, Any],
    git_remote: dict[str, Any],
    provider: str,
    user_text: str = "",
) -> SoloEligibilityResult:
    cfg = load_solo_execution_config()
    if not is_solo_execution_mode_enabled():
        return SoloEligibilityResult(ok=False, blocker_code="SOLO_EXECUTION_DISABLED")

    settings = get_settings()
    if not settings.mutation_execution_enabled:
        return SoloEligibilityResult(
            ok=False,
            blocker_code="SOLO_MUTATION_EXECUTION_DISABLED",
            detail="Set MUTATION_EXECUTION_ENABLED=true for governed solo execution.",
            required_action="Enable mutation execution locally, then retry.",
            safe_next_command="Deploy AethOS to Railway with env vars and verify it.",
        )

    if _DESTRUCTIVE_RX.search(user_text or ""):
        return SoloEligibilityResult(
            ok=False,
            blocker_code="SOLO_DESTRUCTIVE_ACTION_BLOCKED",
            detail="Solo execution mode does not permit destructive actions.",
            required_action="Remove destructive language from the request.",
        )

    provider_norm = str(provider or "").strip().lower()
    if cfg.provider_scope and provider_norm != cfg.provider_scope:
        return SoloEligibilityResult(
            ok=False,
            blocker_code="SOLO_PROVIDER_SCOPE_MISMATCH",
            detail=f"Solo provider scope is `{cfg.provider_scope}`.",
        )
    if cfg.allowed_providers and provider_norm not in cfg.allowed_providers:
        return SoloEligibilityResult(
            ok=False,
            blocker_code="SOLO_PROVIDER_NOT_ALLOWED",
            detail=f"Provider `{provider_norm}` is not in the solo allowlist.",
        )

    repo = _normalize_repo_slug(str(git_remote.get("repository") or plan.get("repo") or ""))
    allowed_repos = tuple(_normalize_repo_slug(item) for item in cfg.allowed_repos)
    if allowed_repos and repo not in allowed_repos:
        return SoloEligibilityResult(
            ok=False,
            blocker_code="SOLO_REPO_NOT_ALLOWED",
            detail=f"Repository `{repo or 'unknown'}` is not in the solo allowlist.",
            required_action="Add the repo to AETHOS_SOLO_ALLOWED_REPOS or disable solo mode.",
        )

    environment = str(plan.get("environment") or "").strip().lower()
    if is_production_environment(environment) and not cfg.allow_production:
        return SoloEligibilityResult(
            ok=False,
            blocker_code="SOLO_PRODUCTION_NOT_ALLOWED",
            detail="Production targets require AETHOS_SOLO_ALLOW_PRODUCTION=true.",
            required_action="Use a staging environment or enable solo production explicitly.",
            safe_next_command="Deploy AethOS to Railway staging with env vars and verify it.",
        )
    if cfg.allowed_environments and environment and environment not in cfg.allowed_environments:
        return SoloEligibilityResult(
            ok=False,
            blocker_code="SOLO_ENVIRONMENT_NOT_ALLOWED",
            detail=f"Environment `{environment}` is not in the solo allowlist.",
        )

    missing_env = _missing_secure_env_names(env_report, plan=plan, provider=provider_norm)
    if missing_env:
        return SoloEligibilityResult(
            ok=False,
            blocker_code="SOLO_MISSING_ENV_REFERENCE",
            detail=f"Required env vars missing from secure store: {', '.join(missing_env)}",
            required_action="Store required env values in the credential vault or secure store.",
            safe_next_command="show railway credential diagnostics",
            missing_env_names=missing_env,
        )

    return SoloEligibilityResult(ok=True)


def build_solo_railway_execution_policy(
    *,
    plan: dict[str, Any],
    user_text: str = "",
) -> RailwayExecutionEnablementPolicy:
    from aethos_core.config import get_settings
    from aethos_core.governance.approval_privacy_governance import (
        solo_auto_approve_phases,
        solo_auto_approve_preflight,
    )
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        extract_final_phrase_from_text,
        validate_final_phrase,
    )

    cfg = load_solo_execution_config()
    settings = get_settings()
    project = str(plan.get("project") or "").strip().lower()
    environment = str(plan.get("environment") or "").strip().lower()
    service = str(plan.get("service_name") or "").strip().lower()
    is_production = is_production_environment(environment)
    phrase = extract_final_phrase_from_text(user_text)
    phrase_required = cfg.require_final_confirmation
    phrase_valid = validate_final_phrase(phrase=phrase, is_production=is_production) if phrase else False
    phase_override = solo_auto_approve_phases()
    return RailwayExecutionEnablementPolicy(
        mode="enabled",
        greenfield_execution_enabled=True,
        allowed=True,
        dry_run_only=False,
        production_allowed=cfg.allow_production,
        final_phrase_required=phrase_required,
        final_phrase_provided=bool(phrase),
        final_phrase_valid=phrase_valid if phrase_required else True,
        target_project=project,
        target_environment=environment,
        target_service=service,
        is_production=is_production,
        allowlist_passed=True,
        target_loaded=True,
        next_step="",
        blocking_reasons=[],
        blocking_reason_messages=[],
        solo_execution_override=phase_override,
        solo_phase_override=phase_override,
        solo_preflight_auto_approve=solo_auto_approve_preflight(),
    )


def compose_solo_greenfield_intro(
    *,
    plan: dict[str, Any],
    git_remote: dict[str, Any],
    env_report: dict[str, Any],
    local_source: dict[str, Any],
    inspection: dict[str, Any] | None = None,
) -> str:
    inspection = inspection or {}
    env_names = list(env_report.get("required_env_var_names") or [])
    lines = [
        "No existing Railway service matched AethOS.",
        "",
        "I can create a new Railway project/service from your local workspace.",
        "",
        "Detected:",
        f"- Repo: `{git_remote.get('repository') or plan.get('repo')}`",
        f"- Branch: `{git_remote.get('branch') or plan.get('branch')}`",
        f"- Stack: {inspection.get('runtime') or plan.get('runtime') or 'unknown'}",
        f"- Required env vars: **{len(env_names)}** (names only)",
        f"- Target environment: `{plan.get('environment')}`",
        "",
        "Proceeding under **solo execution mode**.",
    ]
    return "\n".join(lines)


def _missing_secure_env_names(env_report: dict[str, Any], *, plan: dict[str, Any], provider: str = "") -> list[str]:
    from aethos_core.providers.railway.env_value_readiness.env_classification import (
        EnvCriticality,
        classify_env_var,
        infer_deployment_profile,
    )
    from aethos_core.providers.railway.env_value_readiness.env_deployment_filter import (
        filter_greenfield_deployment_env_var_names,
    )
    from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
        resolve_env_var_from_secure_store,
    )

    profile = infer_deployment_profile(plan)
    names = filter_greenfield_deployment_env_var_names(
        list(env_report.get("required_env_var_names") or []),
        plan=plan,
    )
    provider_norm = str(provider or plan.get("provider") or "").strip().lower()
    if provider_norm == "vercel":
        from aethos_core.providers.vercel.greenfield_deployment.build_env_criticality import (
            list_build_critical_env_names,
        )

        framework = str(plan.get("framework") or "nextjs")
        names = list_build_critical_env_names(names, framework=framework)

    missing: list[str] = []
    for name in names:
        upper = str(name).strip().upper()
        if provider_norm != "vercel" and classify_env_var(upper, profile=profile) != EnvCriticality.CRITICAL_SECRET:
            continue
        resolved = resolve_env_var_from_secure_store(upper, plan=plan)
        if resolved.ok:
            continue
        missing.append(upper)
    return missing
