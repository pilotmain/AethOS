# SPDX-License-Identifier: Apache-2.0
"""APPROVAL_PRIVACY_REHARDENING_001 — centralized governance flags and diagnostics."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_LOCAL_ENV_WARNING_EMITTED = False


def is_autonomous_execution_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(get_settings().autonomous_execution_enabled)


def is_local_env_trusted() -> bool:
    from aethos_core.config import get_settings

    return bool(get_settings().aethos_local_env_trusted)


def local_env_trusted_or_empty() -> bool:
    """Return True when local env reads are permitted."""
    trusted = is_local_env_trusted()
    if not trusted:
        return False
    global _LOCAL_ENV_WARNING_EMITTED
    if not _LOCAL_ENV_WARNING_EMITTED:
        logger.warning(
            "AETHOS_LOCAL_ENV_TRUSTED=true — process env and .env.local may be used for mutation secrets."
        )
        _LOCAL_ENV_WARNING_EMITTED = True
    return True


def solo_auto_approve_preflight() -> bool:
    from aethos_core.config import get_settings

    settings = get_settings()
    return bool(settings.aethos_solo_execution_mode and settings.aethos_solo_auto_approve)


def solo_auto_approve_phases() -> bool:
    from aethos_core.config import get_settings

    settings = get_settings()
    return bool(settings.aethos_solo_execution_mode and settings.aethos_solo_auto_approve_phases)


def browser_capture_requires_approval() -> bool:
    from aethos_core.config import get_settings

    return bool(get_settings().browser_capture_approval_required)


def credential_live_validation_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(get_settings().credential_live_validation_enabled)


def chat_presentation_bypass_allowed(*, channel: str = "chat") -> bool:
    """Full engineering journal dumps are MC-only by default."""
    from aethos_core.config import get_settings

    settings = get_settings()
    if channel in {"mc", "mission_control", "engineering"}:
        return bool(settings.presentation_bypass_mc_enabled)
    return bool(settings.presentation_bypass_chat_enabled)


def governance_diagnostics_snapshot() -> dict[str, Any]:
    from aethos_core.config import get_settings
    from aethos_core.governance.governance_override_store import effective_bool_flag
    from aethos_core.solo_execution.solo_execution_mode import load_solo_execution_config

    settings = get_settings()
    solo = load_solo_execution_config()
    fast_path_active = any(
        (
            solo.enabled,
            settings.aethos_solo_auto_approve,
            settings.aethos_solo_auto_approve_phases,
            settings.aethos_local_env_trusted,
        )
    )
    return {
        "mutation_execution_enabled": effective_bool_flag("mutation_execution_enabled"),
        "railway_greenfield_mutation_kill_switch": effective_bool_flag("railway_greenfield_mutation_kill_switch"),
        "autonomous_execution_enabled": bool(settings.autonomous_execution_enabled),
        "aethos_solo_execution_mode": bool(settings.aethos_solo_execution_mode),
        "aethos_solo_auto_approve": bool(settings.aethos_solo_auto_approve),
        "aethos_solo_auto_approve_phases": bool(settings.aethos_solo_auto_approve_phases),
        "aethos_local_env_trusted": bool(settings.aethos_local_env_trusted),
        "aethos_solo_allow_production": bool(settings.aethos_solo_allow_production),
        "aethos_solo_require_final_confirmation": bool(settings.aethos_solo_require_final_confirmation),
        "browser_capture_approval_required": bool(settings.browser_capture_approval_required),
        "credential_live_validation_enabled": bool(settings.credential_live_validation_enabled),
        "presentation_bypass_chat_enabled": bool(settings.presentation_bypass_chat_enabled),
        "presentation_bypass_mc_enabled": bool(settings.presentation_bypass_mc_enabled),
        "local_fast_path_active": fast_path_active,
        "vercel_greenfield_phased_enablement": bool(settings.vercel_greenfield_phased_enablement),
    }
