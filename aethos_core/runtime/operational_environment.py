# SPDX-License-Identifier: Apache-2.0
"""Operational environment awareness — dev, staging, production labels for all operator surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_CANONICAL_ENVS = frozenset({"development", "staging", "production", "local"})


@dataclass(frozen=True)
class OperationalEnvironmentSnapshot:
    canonical: str
    display_label: str
    app_env: str
    deployment_mode: str
    trigger_env: str
    mutation_scope: str
    production_mutations_unlocked: bool
    banner: str

    def to_dict(self) -> dict[str, Any]:
        from aethos_core.security.secret_redaction import redact_value

        return redact_value(
            {
                "canonical": self.canonical,
                "display_label": self.display_label,
                "app_env": self.app_env,
                "deployment_mode": self.deployment_mode,
                "trigger_env": self.trigger_env,
                "mutation_scope": self.mutation_scope,
                "production_mutations_unlocked": self.production_mutations_unlocked,
                "banner": self.banner,
            }
        )


def resolve_operational_environment() -> OperationalEnvironmentSnapshot:
    from aethos_core.config import get_settings

    settings = get_settings()
    override = str(getattr(settings, "operational_environment", "") or "").strip().lower()
    app_env = str(settings.app_env or "development").strip().lower()
    deployment_mode = str(settings.deployment_mode or "local").strip().lower()
    trigger_env = str(settings.trigger_env or "dev").strip().lower()

    canonical = _canonical_from_parts(override=override, app_env=app_env, deployment_mode=deployment_mode, trigger_env=trigger_env)
    display = _display_label(canonical)
    prod_unlocked = bool(settings.mutation_t3_production_enabled and settings.mutation_execution_enabled)
    mutation_scope = "production" if prod_unlocked and canonical == "production" else _default_mutation_scope(canonical)

    banner = (
        f"**Environment:** `{display}` (`{canonical}`) · deployment `{deployment_mode}` · "
        f"mutations scoped to **{mutation_scope}**"
    )
    if canonical == "production" and not prod_unlocked:
        banner += " · production mutations **locked** (enable `MUTATION_T3_PRODUCTION_ENABLED` to unlock)"

    return OperationalEnvironmentSnapshot(
        canonical=canonical,
        display_label=display,
        app_env=app_env,
        deployment_mode=deployment_mode,
        trigger_env=trigger_env,
        mutation_scope=mutation_scope,
        production_mutations_unlocked=prod_unlocked,
        banner=banner,
    )


def environment_banner(*, compact: bool = False) -> str:
    snap = resolve_operational_environment()
    if compact:
        return f"[{snap.display_label}]"
    return snap.banner


def stamp_external_channel_reply(reply: str, *, channel: str) -> str:
    """Return the reply unchanged.

    Historically this prefixed external-channel replies (Telegram/SMS/Discord)
    with the environment banner so operators knew which environment answered. That
    stamped *every* message — including casual chit-chat — which operators found
    noisy, so the banner is no longer prepended on any channel. The environment is
    still available on demand via `/runtime/status` and the operator CLI
    (`environment_banner()`); it just isn't injected into conversational replies.
    """
    return reply


def assert_environment_allowed(*, target_environment: str, operation: str = "mutation") -> tuple[bool, str]:
    """Governed check before cloud mutations — returns (allowed, detail)."""
    snap = resolve_operational_environment()
    target = (target_environment or snap.mutation_scope or "staging").strip().lower()
    if target in {"prod", "production"}:
        if snap.canonical != "production" and not snap.production_mutations_unlocked:
            return False, (
                f"{operation} targeting **production** blocked in `{snap.display_label}` runtime. "
                "Set `APP_ENV=production` and unlock production mutations explicitly."
            )
        if not snap.production_mutations_unlocked:
            return False, "Production mutations require `MUTATION_EXECUTION_ENABLED` and `MUTATION_T3_PRODUCTION_ENABLED`."
    return True, f"Allowed in `{snap.display_label}` for target `{target}`."


def _canonical_from_parts(*, override: str, app_env: str, deployment_mode: str, trigger_env: str) -> str:
    if override in _CANONICAL_ENVS:
        return override
    if override in {"dev", "development"}:
        return "development"
    if override in {"stage", "staging"}:
        return "staging"
    if override in {"prod", "production"}:
        return "production"
    if app_env in {"production", "prod"}:
        return "production"
    if app_env in {"staging", "stage"}:
        return "staging"
    if trigger_env in {"production", "prod"}:
        return "production"
    if trigger_env in {"staging", "stage"}:
        return "staging"
    if deployment_mode in {"hosted", "enterprise", "edge"} and app_env not in {"development", "dev"}:
        return "staging" if app_env in {"staging", "stage"} else "production" if app_env in {"production", "prod"} else "staging"
    return "development" if app_env in {"development", "dev", ""} else app_env if app_env in _CANONICAL_ENVS else "local"


def _display_label(canonical: str) -> str:
    return {
        "development": "Development",
        "staging": "Staging",
        "production": "Production",
        "local": "Local",
    }.get(canonical, canonical.title())


def _default_mutation_scope(canonical: str) -> str:
    if canonical == "production":
        return "production"
    if canonical == "staging":
        return "staging"
    return "staging"
