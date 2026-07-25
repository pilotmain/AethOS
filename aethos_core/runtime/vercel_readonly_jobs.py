# SPDX-License-Identifier: Apache-2.0
"""Vercel read-only inspection jobs and mutating-request guards."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_intents import (
    is_vercel_inspection_request,
    is_vercel_mutation_request,
)
from aethos_core.runtime.browser_profiles import (
    BrowserProfile,
    BrowserProfileStatus,
    PersistenceMode,
    authorization_status_for_profile,
    is_profile_reusable_for_inspection,
    normalize_site,
    profile_auth_snapshot,
)

VERCEL_READONLY_JOB_TYPES = frozenset(
    {
        "vercel_projects_inventory",
        "vercel_service_health_summary",
        "vercel_deployment_status_summary",
    }
)

_PERSISTENCE_RANK = {
    PersistenceMode.PERSISTENT.value: 0,
    PersistenceMode.EXPIRES_30D.value: 1,
    PersistenceMode.EXPIRES_7D.value: 2,
    PersistenceMode.USE_ONCE.value: 3,
}


def infer_vercel_mutating_intent(text: str) -> bool:
    return is_vercel_mutation_request(text)


def infer_vercel_readonly_job(text: str) -> tuple[str, str, dict[str, Any]] | None:
    """Return (title, job_type, params) or None."""
    raw = (text or "").strip()
    if not raw or not is_vercel_inspection_request(raw):
        return None
    from aethos_core.operational_target_resolution.provider_intent_guard import (
        blocks_provider_readonly_diagnostics_route,
        should_infer_vercel_readonly_from_text,
    )

    if blocks_provider_readonly_diagnostics_route(raw):
        return None
    if not re.search(r"\bvercel\b", raw, re.I):
        return None
    lower = raw.lower()
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import extract_vercel_project_hint

    project = extract_vercel_project_hint(raw)
    params: dict[str, Any] = {"user_request": raw, "site": "vercel.com", "scope": "vercel"}
    if project:
        params["project_name"] = project
        params["project_hint"] = project

    if project and re.search(r"\b(error|fail|log|health|status|fix|diagnos)\b", lower):
        return (
            f"Vercel deployment diagnostics — {project}",
            "vercel_deployment_status_summary",
            params,
        )
    if re.search(r"\b(deployment|deployments)\b", lower) and re.search(
        r"\b(status|summary)\b", lower
    ):
        return (
            "Vercel deployment status summary",
            "vercel_deployment_status_summary",
            {**params, "user_request": raw, "site": "vercel.com", "scope": "vercel"},
        )
    if re.search(r"\b(health|healthy|down|status)\b", lower) and re.search(
        r"\b(service|services|app|apps|project|projects)\b", lower
    ):
        return (
            "Vercel service health summary",
            "vercel_service_health_summary",
            {**params, "user_request": raw, "site": "vercel.com", "scope": "vercel"},
        )
    return (
        "Vercel projects inventory",
        "vercel_projects_inventory",
        {**params, "user_request": raw, "site": "vercel.com", "scope": "vercel"},
    )


def mutating_request_blocked_reply() -> str:
    return (
        "I can **inspect** your Vercel dashboard read-only and **prepare proposals**, "
        "but **mutation actions are not enabled yet** (restart, redeploy, delete, env changes).\n\n"
        "When write actions are added, they will require explicit approval and verification."
    )


def vercel_readonly_needs_session_reply() -> str:
    return (
        "I need a **supervised Vercel browser session** first.\n\n"
        "1. Ask to open Vercel in browser automation and **approve** in Mission Control → Jobs.\n"
        "2. **Log in manually** in the opened browser window.\n"
        "3. Optionally choose **Save session** for future read-only checks (default is use-once only).\n\n"
        "AethOS does **not** store passwords or ask for credentials in chat."
    )


def vercel_readonly_session_expired_reply() -> str:
    return (
        "I found a saved Vercel session, but it appears **expired**.\n\n"
        "Open a supervised browser session, log in manually, then **Save session** "
        "if you want future read-only checks."
    )


def vercel_readonly_profile_not_persistent_reply() -> str:
    return (
        "I found a saved Vercel session saved as **use once only**, so it cannot be reused "
        "for read-only inspection.\n\n"
        "Open a supervised session, log in, then save with **Save until I remove it** "
        "or **Save for 7 days**."
    )


def vercel_readonly_saved_profile_runtime_blocked_reply(
    profile_id: str,
    *,
    runtime_message: str,
) -> str:
    return (
        "I found your **saved Vercel session**, but browser execution is currently blocked "
        "by an AethOS runtime issue.\n\n"
        f"**Profile:** `{profile_id}`\n"
        f"**Runtime:** {runtime_message}\n\n"
        "Your authorization is still saved. After the runtime fix or API restart, "
        "I can reuse it without asking you to log in again."
    )


def _is_vercel_profile(profile: BrowserProfile) -> bool:
    return profile.scope == "vercel" or normalize_site(profile.site) == "vercel.com"


def _vercel_profile_sort_key(profile: BrowserProfile) -> tuple[int, int, float]:
    reusable = is_profile_reusable_for_inspection(profile)
    rank = _PERSISTENCE_RANK.get(profile.persistence_mode, 9)
    return (0 if reusable else 1, rank, -profile.created_at)


def _list_vercel_profiles() -> list[BrowserProfile]:
    browser_profile_store.list_all(refresh=True)
    candidates: list[BrowserProfile] = []
    for profile in browser_profile_store.list_all(refresh=False):
        if not _is_vercel_profile(profile):
            continue
        if profile.status == BrowserProfileStatus.REVOKED:
            continue
        candidates.append(profile)
    candidates.sort(key=_vercel_profile_sort_key)
    return candidates


def latest_saved_vercel_profile() -> BrowserProfile | None:
    profiles = _list_vercel_profiles()
    return profiles[0] if profiles else None


def latest_reusable_vercel_profile() -> BrowserProfile | None:
    for profile in _list_vercel_profiles():
        if is_profile_reusable_for_inspection(profile):
            return profile
    return None


def resolve_vercel_profile_for_chat() -> tuple[str | None, str | None]:
    """
    Return (active_profile_id, block_reason).
    block_reason is 'expired' | 'not_persistent' | 'missing' when chat must not create a job.
    """
    from pathlib import Path

    reusable = latest_reusable_vercel_profile()
    if reusable:
        return reusable.profile_id, None

    saved = latest_saved_vercel_profile()
    if not saved:
        return None, "missing"

    storage_exists = Path(saved.storage_path).is_file()
    if not storage_exists:
        return None, "expired"

    auth = authorization_status_for_profile(saved)
    if auth == "expired" or saved.status == BrowserProfileStatus.EXPIRED:
        return None, "expired"

    if saved.persistence_mode == PersistenceMode.USE_ONCE.value:
        return None, "not_persistent"

    if saved.status == BrowserProfileStatus.REVOKED:
        return None, "missing"

    if saved.status != BrowserProfileStatus.ACTIVE:
        return saved.profile_id, None

    return saved.profile_id, None


def saved_vercel_profile_auth_for_chat() -> dict[str, Any] | None:
    profile = latest_saved_vercel_profile()
    if not profile:
        return None
    return profile_auth_snapshot(profile)


def active_vercel_profile_id() -> str | None:
    profile = latest_reusable_vercel_profile()
    return profile.profile_id if profile else None


def resolve_vercel_auth_for_chat() -> dict[str, str | None]:
    """Return auth_method, credential_id, profile_id, token, block_reason, detail."""
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    adapter = VercelAuthAdapter()
    resolved = adapter.resolve_best_auth_method(operation="read_projects")
    method = resolved.get("method")
    if method == "api_token":
        credential_id = str(resolved.get("credential_id") or "")
        token = adapter.get_api_token(credential_id) if credential_id else ""
        if not token:
            return {
                "auth_method": "api_token",
                "credential_id": credential_id,
                "profile_id": None,
                "token": None,
                "block_reason": "missing",
                "detail": "Vercel API token could not be loaded from the credential vault.",
            }
        return {
            "auth_method": "api_token",
            "credential_id": credential_id,
            "profile_id": None,
            "token": token,
            "block_reason": None,
            "detail": None,
        }
    if method == "browser":
        profile_id, block = resolve_vercel_profile_for_chat()
        return {
            "auth_method": "browser",
            "credential_id": None,
            "profile_id": profile_id,
            "token": None,
            "block_reason": block,
            "detail": str(resolved.get("detail") or "") or None,
        }
    if method == "cli":
        profile_id, block = resolve_vercel_profile_for_chat()
        return {
            "auth_method": "browser" if profile_id else None,
            "credential_id": None,
            "profile_id": profile_id,
            "token": None,
            "block_reason": block,
            "detail": str(resolved.get("detail") or "") or None,
        }
    return {
        "auth_method": None,
        "credential_id": None,
        "profile_id": None,
        "token": None,
        "block_reason": "missing",
        "detail": str(resolved.get("detail") or "No Vercel auth configured."),
    }


def resolve_vercel_api_token_for_chat() -> tuple[str, str]:
    """Return (token, credential_id) for governed Vercel mutations."""
    auth = resolve_vercel_auth_for_chat()
    token = str(auth.get("token") or "").strip()
    credential_id = str(auth.get("credential_id") or "")
    if token:
        return token, credential_id
    from aethos_core.providers.vercel.auth import VercelAuthAdapter

    adapter = VercelAuthAdapter()
    resolved = adapter.resolve_best_auth_method(operation="read_projects")
    credential_id = str(resolved.get("credential_id") or "")
    token = adapter.get_api_token(credential_id) if credential_id else ""
    return str(token or "").strip(), credential_id


def vercel_connect_required_reply() -> str:
    return (
        "I need a **Vercel connection** before I can list your apps.\n\n"
        "Open **Mission Control → Advanced settings → Credentials → Vercel** and either:\n"
        "- **Add API token** (recommended — survives restarts), or\n"
        "- **Save a browser session** after supervised login.\n\n"
        "AethOS never asks for tokens or passwords in chat."
    )
