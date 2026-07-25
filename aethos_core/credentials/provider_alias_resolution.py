# SPDX-License-Identifier: Apache-2.0
"""Map Credential Center display names and env keys to canonical provider keys."""

from __future__ import annotations

import os
from typing import Any

from aethos_core.connections.models import CredentialRecord

_PROVIDER_ALIAS_SETS: dict[str, frozenset[str]] = {
    "railway": frozenset(
        {
            "railway",
            "railway primary account",
            "railway_api_token",
        }
    ),
    "github": frozenset(
        {
            "github",
            "github primary account",
            "github_api_token",
            "github_token",
        }
    ),
    "vercel": frozenset(
        {
            "vercel",
            "vercel primary account",
            "vercel_api_token",
        }
    ),
}


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def normalize_canonical_provider(key: str) -> str | None:
    """Resolve a provider key, label, or env var name to a canonical provider id."""
    normalized = _norm(key)
    if not normalized:
        return None
    for canonical, aliases in _PROVIDER_ALIAS_SETS.items():
        if normalized == canonical or normalized in aliases:
            return canonical
    return None


def provider_alias_set(canonical: str) -> frozenset[str]:
    return _PROVIDER_ALIAS_SETS.get(canonical, frozenset({_norm(canonical)}))


def _value_matches_aliases(value: str, aliases: frozenset[str]) -> bool:
    return _norm(value) in aliases


def canonical_provider_for_credential_record(rec: CredentialRecord) -> str | None:
    """Infer canonical provider from credential metadata (provider field, then label)."""
    by_provider = normalize_canonical_provider(rec.provider)
    if by_provider:
        return by_provider
    return normalize_canonical_provider(rec.label)


def credential_matches_canonical(rec: CredentialRecord, canonical: str) -> bool:
    """
    True when this credential belongs to the canonical provider.

    Explicit provider fields for a different canonical provider win over label aliases.
    """
    aliases = provider_alias_set(canonical)
    rec_provider_canonical = normalize_canonical_provider(rec.provider)
    if rec_provider_canonical and rec_provider_canonical != canonical:
        return False
    if _value_matches_aliases(rec.provider, aliases):
        return True
    if rec_provider_canonical == canonical:
        return True
    if not rec_provider_canonical and _value_matches_aliases(rec.label, aliases):
        return True
    return False


def list_credentials_for_canonical(canonical: str) -> list[CredentialRecord]:
    from aethos_core.security.credential_vault import get_credential_vault

    canonical = normalize_canonical_provider(canonical) or _norm(canonical)
    if not canonical:
        return []
    matched = [
        rec
        for rec in get_credential_vault().list_credentials()
        if credential_matches_canonical(rec, canonical)
    ]
    matched.sort(key=lambda rec: rec.created_at, reverse=True)
    return matched


def _first_decryptable_api_token(creds: list[CredentialRecord]) -> CredentialRecord | None:
    from aethos_core.connections.credential_state import resolve_credential_state

    for rec in creds:
        if rec.revoked or rec.type.value != "api_token":
            continue
        state = resolve_credential_state(rec.credential_id)
        if state.get("decryptable"):
            return rec
    return None


def resolve_latest_decryptable_credential_id(canonical: str) -> tuple[str | None, str]:
    """
    Return (credential_id, resolution_source).

    resolution_source is one of: strict_canonical, credential_center_alias, none
    """
    from aethos_core.security.credential_vault import get_credential_vault

    canonical = normalize_canonical_provider(canonical) or _norm(canonical)
    if not canonical:
        return None, "none"

    strict = get_credential_vault().list_credentials(provider=canonical)
    strict_rec = _first_decryptable_api_token(strict)
    if strict_rec:
        return strict_rec.credential_id, "strict_canonical"

    alias_rec = _first_decryptable_api_token(list_credentials_for_canonical(canonical))
    if alias_rec:
        return alias_rec.credential_id, "credential_center_alias"

    return None, "none"


def env_token_for_canonical_provider(canonical: str) -> str | None:
    canonical = normalize_canonical_provider(canonical) or _norm(canonical)
    if canonical == "railway":
        from aethos_core.config import get_settings

        settings = get_settings()
        token = str(getattr(settings, "railway_api_token", "") or "").strip()
        if token:
            return token
        return str(os.environ.get("RAILWAY_API_TOKEN") or "").strip() or None
    if canonical == "github":
        return str(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip() or None
    if canonical == "vercel":
        return str(os.environ.get("VERCEL_API_TOKEN") or "").strip() or None
    return None


# --- Credentialed execution: vault → process environment injection -------------
# The env var names each provider's CLI/API expects. The vault token is mapped to
# every listed name (CLIs differ on which they read). Injected only at execution,
# scoped to the sandboxed process, never written to disk or the command string.
PROVIDER_CLI_ENV_NAMES: dict[str, tuple[str, ...]] = {
    "railway": ("RAILWAY_TOKEN", "RAILWAY_API_TOKEN"),
    "vercel": ("VERCEL_TOKEN",),
    "supabase": ("SUPABASE_ACCESS_TOKEN",),
    "stripe": ("STRIPE_API_KEY",),
    "resend": ("RESEND_API_KEY",),
    "redis": ("REDIS_URL",),
    "github": ("GH_TOKEN", "GITHUB_TOKEN"),
}


def _vault_token_for_provider(provider: str) -> str | None:
    """Latest decryptable vault token for a provider (any provider name)."""
    from aethos_core.security.credential_vault import get_credential_vault

    credential_id, _source = resolve_latest_decryptable_credential_id(provider)
    if not credential_id:
        # Generic providers (stripe/resend/redis/supabase) may not have a canonical
        # alias set — fall back to a strict provider-name match.
        strict = _first_decryptable_api_token(
            get_credential_vault().list_credentials(provider=_norm(provider))
        )
        credential_id = strict.credential_id if strict else None
    if not credential_id:
        return None
    secret = get_credential_vault().retrieve_secret(credential_id) or {}
    token = str(secret.get("token") or "").strip()
    return token or None


def build_provider_cli_env(provider: str) -> dict[str, Any]:
    """Resolve credentials for a provider and map them to the env vars its CLI/API
    expects. Returns {env, secrets, missing, provider, detail}.

    - `env`: overlay to merge into the sandboxed process environment.
    - `secrets`: raw secret values to redact from captured output.
    - `missing`: True when the provider needs a credential and none is in the vault.
    Credentials are read here only at execution time and are never logged.
    """
    canonical = _norm(provider)
    if canonical in ("shell", "", "none"):
        return {"env": {}, "secrets": [], "missing": False, "provider": canonical, "detail": ""}

    names = PROVIDER_CLI_ENV_NAMES.get(canonical)
    if not names:
        # Unknown provider — run as plain shell (allowlisted binaries only), no creds.
        return {"env": {}, "secrets": [], "missing": False, "provider": canonical, "detail": ""}

    token = _vault_token_for_provider(canonical)
    if not token:
        # Canonical env/settings token (railway/github/vercel) before raw env names.
        token = env_token_for_canonical_provider(canonical)
    if not token:
        # Honest env fallback: an operator may have set the value in the environment.
        token = next((v for v in (os.environ.get(n) for n in names) if v), None)
    if not token:
        return {
            "env": {},
            "secrets": [],
            "missing": True,
            "provider": canonical,
            "detail": f"Needs a {canonical} token in the Mission Control vault (Connections).",
        }

    env: dict[str, str] = {name: token for name in names}
    secrets: list[str] = [token]

    # Provider-specific non-secret/auxiliary env.
    from aethos_core.config import get_settings

    settings = get_settings()
    if canonical == "vercel":
        team_id = str(getattr(settings, "vercel_team_id", "") or "").strip()
        if team_id:
            env["VERCEL_TEAM_ID"] = team_id
    if canonical == "supabase":
        url = str(getattr(settings, "next_public_supabase_url", "") or "").strip()
        if url:
            env["NEXT_PUBLIC_SUPABASE_URL"] = url
        service_role = str(getattr(settings, "supabase_service_role_key", "") or "").strip()
        if service_role:
            env["SUPABASE_SERVICE_ROLE_KEY"] = service_role
            secrets.append(service_role)

    return {"env": env, "secrets": secrets, "missing": False, "provider": canonical, "detail": ""}


def probe_railway_credential_resolution() -> dict[str, Any]:
    """Structured probe for `debug railway credential resolution` (no secret values)."""
    from aethos_core.security.credential_vault import get_credential_vault

    canonical = "railway"
    strict = get_credential_vault().list_credentials(provider=canonical)
    strict_rec = _first_decryptable_api_token(strict)
    alias_rec = _first_decryptable_api_token(list_credentials_for_canonical(canonical))

    canonical_key_lookup_pass = strict_rec is not None
    alias_lookup_pass = alias_rec is not None and (
        strict_rec is None or strict_rec.credential_id != alias_rec.credential_id
    )

    credential_id, resolution_source = resolve_latest_decryptable_credential_id(canonical)

    return {
        "canonical_key_lookup_pass": canonical_key_lookup_pass,
        "alias_lookup_pass": alias_lookup_pass,
        "strict_credential_count": len(strict),
        "alias_credential_count": len(list_credentials_for_canonical(canonical)),
        "credential_id": credential_id or "",
        "alias_resolution_source": resolution_source,
        "resolved_provider": canonical if credential_id else "",
    }

