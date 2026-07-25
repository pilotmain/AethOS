# SPDX-License-Identifier: Apache-2.0
"""P4.1 — Vercel greenfield phased enablement (parity with Railway FIX 108–114)."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.config import get_settings


@dataclass(frozen=True)
class VercelPhaseEnablement:
    connect_repo: bool
    configure_env: bool
    trigger_deploy: bool
    verify_runtime: bool
    phased_mode: bool


def load_vercel_phase_enablement(*, solo_phase_override: bool = False) -> VercelPhaseEnablement:
    settings = get_settings()
    phased = bool(settings.vercel_greenfield_phased_enablement)
    if solo_phase_override and phased:
        return VercelPhaseEnablement(
            connect_repo=True,
            configure_env=True,
            trigger_deploy=True,
            verify_runtime=True,
            phased_mode=True,
        )
    return VercelPhaseEnablement(
        connect_repo=bool(getattr(settings, "vercel_greenfield_connect_repo_enabled", False)),
        configure_env=bool(getattr(settings, "vercel_greenfield_configure_env_enabled", False)),
        trigger_deploy=bool(getattr(settings, "vercel_greenfield_trigger_deploy_enabled", False)),
        verify_runtime=bool(getattr(settings, "vercel_greenfield_verify_runtime_enabled", False)),
        phased_mode=phased,
    )
