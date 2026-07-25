# SPDX-License-Identifier: Apache-2.0
"""Doctor strictness profiles — development break-glass vs production hardening."""

from __future__ import annotations

from typing import Literal

DoctorProfile = Literal["development", "staging", "production", "strict", "relaxed"]

_VALID = frozenset({"development", "staging", "production", "strict", "relaxed"})


def resolve_doctor_profile() -> DoctorProfile:
    from aethos_core.config import get_settings

    settings = get_settings()
    explicit = (getattr(settings, "aethos_doctor_profile", "") or "").strip().lower()
    if explicit in _VALID:
        return explicit  # type: ignore[return-value]

    from aethos_core.runtime.operational_environment import resolve_operational_environment

    canonical = resolve_operational_environment().canonical
    if canonical == "production":
        return "production"
    if canonical == "staging":
        return "staging"
    return "development"


def break_glass_acknowledged() -> bool:
    from aethos_core.config import get_settings

    settings = get_settings()
    return bool(
        getattr(settings, "aethos_operator_break_glass_acknowledged", False)
        or settings.aethos_solo_execution_mode
        or settings.aethos_local_env_trusted
    )


def profile_allows_break_glass_warnings() -> bool:
    profile = resolve_doctor_profile()
    return profile in {"development", "staging", "relaxed"} and break_glass_acknowledged()
