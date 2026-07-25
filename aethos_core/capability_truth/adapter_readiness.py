# SPDX-License-Identifier: Apache-2.0
"""Adapter readiness — verify registered providers and credential configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from aethos_core.capability_truth.provider_capability_matrix import ProviderCapabilitySummary, get_provider_summary


@dataclass
class AdapterReadiness:
    provider: str
    registered: bool
    tier: str
    credentials_configured: bool
    e2e_ready: bool
    notes: list[str] = field(default_factory=list)

    @property
    def operational(self) -> bool:
        return self.registered and self.credentials_configured and self.tier in {"full", "partial"}


def is_provider_registered(provider: str) -> bool:
    try:
        from aethos_core.providers.base.provider_registry import ProviderRegistry

        return ProviderRegistry.get((provider or "").strip().lower()) is not None
    except Exception:
        return False


def _credentials_configured(provider: str) -> tuple[bool, str]:
    name = (provider or "").strip().lower()
    if name == "railway":
        from aethos_core.providers.railway.mutations import resolve_railway_mutation_credentials

        token, _, err = resolve_railway_mutation_credentials()
        return bool(token), err or ""
    if name == "vercel":
        from aethos_core.providers.vercel.auth import VercelAuthAdapter

        auth = VercelAuthAdapter().resolve_best_auth_method(operation="redeploy")
        return bool(str(auth.get("credential_id") or "").strip()), ""
    if name == "github":
        from aethos_core.providers.github.auth import GitHubAuthAdapter

        auth = GitHubAuthAdapter().resolve_best_auth_method(operation="workflow_rerun")
        return bool(str(auth.get("credential_id") or "").strip()), ""
    return False, "Provider adapter is not registered."


def check_adapter_readiness(provider: str) -> AdapterReadiness:
    summary = get_provider_summary(provider)
    name = (provider or "").strip().lower()
    registered = is_provider_registered(name) if summary and summary.registered else False
    creds_ok, cred_note = _credentials_configured(name) if registered else (False, "")
    notes: list[str] = []
    if summary:
        notes.extend(summary.gaps)
    if cred_note:
        notes.append(cred_note)
    return AdapterReadiness(
        provider=name,
        registered=registered,
        tier=summary.tier if summary else "planned",
        credentials_configured=creds_ok,
        e2e_ready=bool(summary and summary.e2e_ready and registered and creds_ok),
        notes=notes,
    )


def get_configured_operational_providers() -> list[AdapterReadiness]:
    ready: list[AdapterReadiness] = []
    for provider in ("railway", "vercel", "github"):
        status = check_adapter_readiness(provider)
        if status.registered and status.credentials_configured:
            ready.append(status)
    return ready
