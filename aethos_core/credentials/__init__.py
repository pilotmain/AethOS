# SPDX-License-Identifier: Apache-2.0
"""Credential requirement guidance for governed mutations."""

from aethos_core.credentials.credential_guidance import (
    build_credential_requirements_for_job,
    compose_missing_credential_reply,
    compose_railway_token_configuration_reply,
    credential_reload_instructions,
    credential_setup_steps,
    detect_missing_credential,
    find_latest_credential_blocked_preflight,
    is_railway_token_configuration_intent,
    rerun_mutation_preflight_for_job,
    route_railway_token_configuration_guidance,
)


def get_provider_api_token(provider: str, *, require_validated: bool = True) -> str | None:
    """Return a provider API token when configured (env or Credential Center)."""
    from aethos_core.credentials.provider_alias_resolution import (
        env_token_for_canonical_provider,
        normalize_canonical_provider,
        resolve_latest_decryptable_credential_id,
    )
    from aethos_core.operations.orchestration.provider_runtime import (
        get_provider_api_token as _get_token,
        resolve_provider_execution_auth,
    )

    canonical = normalize_canonical_provider(provider) or (provider or "").strip().lower()
    if not canonical:
        return None

    if canonical == "railway":
        from aethos_core.providers.railway.credential_truth import resolve_railway_credential

        auth = resolve_provider_execution_auth(canonical)
        explicit_id = str(auth.get("credential_id") or "").strip() or None
        if not explicit_id:
            credential_id, _resolution_source = resolve_latest_decryptable_credential_id(canonical)
            explicit_id = credential_id or None
        resolved = resolve_railway_credential(credential_id=explicit_id)
        if not resolved.ok or not resolved.token:
            return None
        if require_validated and resolved.source == "none":
            return None
        return resolved.token

    env_token = env_token_for_canonical_provider(canonical)
    if env_token:
        return env_token

    credential_id, _resolution_source = resolve_latest_decryptable_credential_id(canonical)
    auth = resolve_provider_execution_auth(canonical)
    if credential_id and not str(auth.get("credential_id") or ""):
        auth = {**auth, "credential_id": credential_id, "auth_method": "api_token"}
    elif credential_id:
        auth = {**auth, "credential_id": credential_id}

    return _get_token(provider=canonical, auth=auth, require_validated=require_validated)


__all__ = [
    "build_credential_requirements_for_job",
    "compose_missing_credential_reply",
    "compose_railway_token_configuration_reply",
    "credential_reload_instructions",
    "credential_setup_steps",
    "detect_missing_credential",
    "find_latest_credential_blocked_preflight",
    "get_provider_api_token",
    "is_railway_token_configuration_intent",
    "rerun_mutation_preflight_for_job",
    "route_railway_token_configuration_guidance",
]
