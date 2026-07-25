# SPDX-License-Identifier: Apache-2.0
"""Railway greenfield execution enablement boundary — policy only, no mutations."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

ExecutionMode = Literal["disabled", "dry_run", "enabled"]

PRODUCTION_FINAL_PHRASE = (
    "I understand this will create a new Railway service in production. Execute governed deployment."
)
NON_PRODUCTION_FINAL_PHRASE = "Execute governed Railway deployment."
ROLLBACK_FINAL_PHRASE = (
    "I understand this will rollback staging Railway mutations. Execute governed rollback."
)

ENABLEMENT_NO_TARGET_NEXT_STEP = (
    "create railway deployment plan for <repo> in <project> / <environment>"
)


@dataclass(frozen=True)
class RailwayExecutionEnablementConfig:
    mode: ExecutionMode
    greenfield_execution_enabled: bool
    allowed_projects: tuple[str, ...]
    allowed_environments: tuple[str, ...]
    allowed_services: tuple[str, ...]
    allow_production: bool
    require_final_phrase: bool


@dataclass(frozen=True)
class RailwayExecutionEnablementPolicy:
    mode: ExecutionMode
    greenfield_execution_enabled: bool
    allowed: bool
    dry_run_only: bool
    production_allowed: bool
    final_phrase_required: bool
    final_phrase_provided: bool
    final_phrase_valid: bool
    target_project: str
    target_environment: str
    target_service: str
    is_production: bool
    allowlist_passed: bool
    target_loaded: bool = False
    next_step: str = ""
    blocking_reasons: list[str] = field(default_factory=list)
    blocking_reason_messages: list[str] = field(default_factory=list)
    solo_execution_override: bool = False
    solo_phase_override: bool = False
    solo_preflight_auto_approve: bool = False

    def allows_contract_progression(self) -> bool:
        """May proceed with execute/journal enrollment (dry_run or enabled policy)."""
        if not self.target_loaded or self.mode == "disabled":
            return False
        return self.allowlist_passed

    def allows_dry_run_phases(self) -> bool:
        return self.mode == "dry_run" and self.allowlist_passed

    def allows_execute_enrollment(self) -> bool:
        """May enroll execution journal / dry-run phases (not real mutation)."""
        if not self.target_loaded or self.mode == "disabled":
            return False
        if not self.allowlist_passed:
            return False
        if self.mode == "enabled" and self.final_phrase_required and not self.final_phrase_valid:
            return False
        return True

    def allows_real_mutation(self) -> bool:
        """Real Railway API mutation when mode=enabled (phase-specific flags apply per adapter)."""
        from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
            is_railway_mutation_kill_switch_active,
        )
        from aethos_core.providers.railway.execution_contract.production_policy import (
            assess_railway_production_policy,
        )

        if is_railway_mutation_kill_switch_active():
            return False
        if not self.allows_execute_enrollment():
            return False
        if self.mode != "enabled" or not self.greenfield_execution_enabled:
            return False
        if self.is_production:
            prod = assess_railway_production_policy(
                plan={
                    "environment": self.target_environment,
                    "project": self.target_project,
                    "service_name": self.target_service,
                },
            )
            if not prod.forward_live_permitted:
                return False
            if not self.production_allowed:
                return False
        return True

    def _solo_phase_bypass(self) -> bool:
        return bool(self.solo_phase_override or self.solo_execution_override)

    def allows_connect_source_mutation(self) -> bool:
        """FIX 109 — live GitHub source binding (disabled by default via env flag)."""
        from aethos_core.config import get_settings

        if not self.allows_real_mutation():
            return False
        if self._solo_phase_bypass():
            return True
        return bool(getattr(get_settings(), "railway_greenfield_connect_source_enabled", False))

    def allows_disconnect_source_rollback(self) -> bool:
        """FIX 111 — live disconnect_repo_source rollback (disabled by default via env flag)."""
        from aethos_core.config import get_settings
        from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
            is_railway_mutation_kill_switch_active,
        )

        if is_railway_mutation_kill_switch_active():
            return False
        if self.mode != "enabled" or not self.greenfield_execution_enabled:
            return False
        if not self.allowlist_passed or not self.target_loaded:
            return False
        if self._solo_phase_bypass():
            return True
        return bool(getattr(get_settings(), "railway_greenfield_disconnect_source_enabled", False))

    def allows_configure_env_mutation(self) -> bool:
        """FIX 112 — live secure-store env writes (disabled by default via env flag)."""
        from aethos_core.config import get_settings

        if not self.allows_real_mutation():
            return False
        if self._solo_phase_bypass():
            return True
        return bool(getattr(get_settings(), "railway_greenfield_configure_env_enabled", False))

    def allows_trigger_deploy_mutation(self) -> bool:
        """FIX 113 — live deploy trigger (disabled by default via env flag)."""
        from aethos_core.config import get_settings

        if not self.allows_real_mutation():
            return False
        if self._solo_phase_bypass():
            return True
        return bool(getattr(get_settings(), "railway_greenfield_trigger_deploy_enabled", False))

    def allows_verify_runtime_readonly(self) -> bool:
        """FIX 114 — readonly runtime verification after deploy (disabled by default)."""
        from aethos_core.config import get_settings

        if not self.allows_real_mutation():
            return False
        if self._solo_phase_bypass():
            return True
        return bool(getattr(get_settings(), "railway_greenfield_verify_runtime_enabled", False))

    def allows_live_rollback_orchestration(self) -> bool:
        """FIX 115 — governed live rollback dispatch (staging only; separate flags per phase)."""
        return self.allows_disconnect_source_rollback() or self.allows_revert_env_rollback()

    def allows_revert_env_rollback(self) -> bool:
        """FIX 115 — live revert_env_writes rollback (disabled by default)."""
        from aethos_core.config import get_settings
        from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
            is_railway_mutation_kill_switch_active,
        )

        if is_railway_mutation_kill_switch_active():
            return False
        if self.mode != "enabled" or not self.greenfield_execution_enabled:
            return False
        if not self.allowlist_passed or not self.target_loaded:
            return False
        if self._solo_phase_bypass():
            return True
        return bool(getattr(get_settings(), "railway_greenfield_revert_env_enabled", False))


def _parse_csv_list(value: str) -> tuple[str, ...]:
    return tuple(item.strip().lower() for item in (value or "").split(",") if item.strip())


def _normalize_mode(raw: str) -> ExecutionMode:
    mode = (raw or "disabled").strip().lower()
    if mode in {"disabled", "dry_run", "enabled"}:
        return mode  # type: ignore[return-value]
    return "disabled"


def is_railway_greenfield_dry_run_mode() -> bool:
    """True when greenfield execution is in orchestration-only dry_run mode."""
    return load_railway_execution_enablement_config().mode == "dry_run"


def load_railway_execution_enablement_config() -> RailwayExecutionEnablementConfig:
    from aethos_core.config import get_settings

    settings = get_settings()
    return RailwayExecutionEnablementConfig(
        mode=_normalize_mode(getattr(settings, "railway_greenfield_execution_mode", "disabled")),
        greenfield_execution_enabled=bool(
            getattr(settings, "railway_greenfield_execution_enabled", False)
        ),
        allowed_projects=_parse_csv_list(
            getattr(settings, "railway_greenfield_allowed_projects", "pilotos")
        ),
        allowed_environments=_parse_csv_list(
            getattr(settings, "railway_greenfield_allowed_environments", "staging,development")
        ),
        allowed_services=_parse_csv_list(
            getattr(settings, "railway_greenfield_allowed_services", "")
        ),
        allow_production=bool(getattr(settings, "railway_greenfield_allow_production", False)),
        require_final_phrase=bool(
            getattr(settings, "railway_greenfield_require_final_phrase", True)
        ),
    )


def is_production_environment(environment: str) -> bool:
    env = (environment or "").strip().lower()
    return env in {"production", "prod", "live"}


def is_rollback_blocked_environment(environment: str) -> bool:
    """FIX 115 — production rollback is never permitted (ignores allow_production)."""
    return is_production_environment(environment)


def extract_final_phrase_from_text(text: str) -> str:
    """Return exact final-approval phrase if present in user text (no fuzzy match)."""
    raw = (text or "").strip()
    if not raw:
        return ""
    for phrase in (PRODUCTION_FINAL_PHRASE, NON_PRODUCTION_FINAL_PHRASE, ROLLBACK_FINAL_PHRASE):
        if phrase in raw:
            return phrase
    return ""


def extract_rollback_phrase_from_text(text: str) -> str:
    raw = (text or "").strip()
    if ROLLBACK_FINAL_PHRASE in raw:
        return ROLLBACK_FINAL_PHRASE
    return ""


def validate_rollback_phrase(*, phrase: str) -> bool:
    return bool(phrase) and phrase == ROLLBACK_FINAL_PHRASE


def plan_has_execution_target(plan: dict[str, Any] | None) -> bool:
    """True when a deployment plan with repo is loaded (canonical execution target)."""
    plan = plan or {}
    return bool(str(plan.get("repo") or "").strip())


def validate_final_phrase(*, phrase: str, is_production: bool) -> bool:
    if not phrase:
        return False
    if is_production:
        return phrase == PRODUCTION_FINAL_PHRASE
    return phrase == NON_PRODUCTION_FINAL_PHRASE


def assess_railway_execution_enablement_policy(
    *,
    plan: dict[str, Any] | None,
    user_text: str = "",
) -> RailwayExecutionEnablementPolicy:
    cfg = load_railway_execution_enablement_config()
    plan = plan or {}
    target_loaded = plan_has_execution_target(plan)
    project = str(plan.get("project") or "").strip().lower()
    environment = str(plan.get("environment") or "").strip().lower()
    service = str(plan.get("service_name") or "").strip().lower()
    is_production = is_production_environment(environment) if target_loaded else False

    phrase = extract_final_phrase_from_text(user_text)
    phrase_valid = validate_final_phrase(phrase=phrase, is_production=is_production) if phrase else False

    allowlist_passed = True
    reasons: list[str] = []
    messages: list[str] = []
    next_step = ""

    if not target_loaded:
        allowlist_passed = False
        reasons.append("no_target_loaded")
        messages.append("No Railway deployment target is loaded.")
        next_step = ENABLEMENT_NO_TARGET_NEXT_STEP
    else:
        if cfg.allowed_projects and project not in cfg.allowed_projects:
            allowlist_passed = False
            reasons.append("project_not_allowlisted")
            messages.append(f"Project `{project}` is not in the greenfield execution allowlist.")
        if cfg.allowed_environments and environment not in cfg.allowed_environments:
            allowlist_passed = False
            reasons.append("environment_not_allowlisted")
            messages.append(
                f"Environment `{environment}` is not in the greenfield execution allowlist."
            )
        if cfg.allowed_services and service and service not in cfg.allowed_services:
            allowlist_passed = False
            reasons.append("service_not_allowlisted")
            messages.append(f"Service `{service}` is not in the greenfield execution allowlist.")

        if is_production and not cfg.allow_production:
            allowlist_passed = False
            reasons.append("production_not_allowed")
            messages.append("Production greenfield execution is not allowed by runtime policy.")

    from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
        is_railway_mutation_kill_switch_active,
    )

    if is_railway_mutation_kill_switch_active():
        reasons.append("mutation_kill_switch_active")
        messages.append("Emergency Railway greenfield mutation kill switch is active.")

    if cfg.mode == "disabled":
        reasons.append("execution_mode_disabled")
        messages.append("Railway greenfield execution mode is disabled.")

    if cfg.mode == "enabled" and cfg.require_final_phrase:
        if not phrase:
            reasons.append("final_phrase_missing")
            messages.append("Final governed execution approval phrase is required but was not provided.")
        elif not phrase_valid:
            reasons.append("final_phrase_invalid")
            messages.append("Final governed execution approval phrase does not match the required exact text.")

    if not cfg.greenfield_execution_enabled and cfg.mode == "enabled":
        reasons.append("greenfield_execution_flag_disabled")
        messages.append("Railway greenfield execution enabled flag is false.")

    allowed = target_loaded and cfg.mode != "disabled" and allowlist_passed
    if cfg.mode == "enabled" and cfg.require_final_phrase and not phrase_valid:
        allowed = False

    production_blockers: list[str] = []
    production_messages: list[str] = []
    if target_loaded and is_production:
        from aethos_core.providers.railway.execution_contract.production_policy import (
            assess_railway_production_policy,
        )

        prod = assess_railway_production_policy(
            plan=plan,
            user_text=user_text,
        )
        production_blockers = list(prod.blockers)
        production_messages = list(prod.messages)
        if production_blockers and cfg.mode == "enabled":
            allowed = False

    merged_reasons = reasons + [c for c in production_blockers if c not in reasons]
    merged_messages = messages + [m for m in production_messages if m not in messages]

    return RailwayExecutionEnablementPolicy(
        mode=cfg.mode,
        greenfield_execution_enabled=cfg.greenfield_execution_enabled,
        allowed=allowed,
        dry_run_only=cfg.mode == "dry_run",
        production_allowed=cfg.allow_production,
        final_phrase_required=cfg.require_final_phrase,
        final_phrase_provided=bool(phrase),
        final_phrase_valid=phrase_valid,
        target_project=project,
        target_environment=environment,
        target_service=service,
        is_production=is_production,
        allowlist_passed=allowlist_passed,
        target_loaded=target_loaded,
        next_step=next_step,
        blocking_reasons=merged_reasons,
        blocking_reason_messages=merged_messages,
    )


_ENABLEMENT_RX = re.compile(r"\bshow\s+railway\s+execution\s+enablement\b", re.I)


def is_railway_execution_enablement_intent(text: str) -> bool:
    return bool(_ENABLEMENT_RX.search((text or "").strip()))


def execution_runtime_allows_real_mutation() -> bool:
    """Whether runtime policy would permit real Railway mutation (still gated elsewhere)."""
    policy = assess_railway_execution_enablement_policy(plan={}, user_text="")
    return policy.allows_real_mutation()
