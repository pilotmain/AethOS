# SPDX-License-Identifier: Apache-2.0
"""Ordered preflight for saved-profile browser work — profile before runtime."""

from __future__ import annotations

from pathlib import Path

from aethos_core.runtime.browser_diagnostics import (
    validate_browser_runtime_for_execution,
)
from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfile, BrowserProfileStatus


class ProfileNotFoundError(RuntimeError):
    layer = "profile_missing"


class ProfileRevokedError(RuntimeError):
    layer = "profile_revoked"


class ProfileExpiredError(RuntimeError):
    layer = "profile_expired"


class ProfileNotActiveError(RuntimeError):
    layer = "profile_not_active"


def preflight_readonly_profile_auth(profile_id: str) -> BrowserProfile:
    """Validate saved authorization only — does not probe Playwright runtime."""
    pid = (profile_id or "").strip()
    if not pid:
        raise ProfileNotFoundError(
            "Saved Vercel session was not found. "
            "Open a supervised Vercel session and save it again."
        )

    profile = browser_profile_store.get(pid)
    if not profile:
        raise ProfileNotFoundError(
            "Saved Vercel session was not found. "
            "Open a supervised Vercel session and save it again."
        )
    if profile.status == BrowserProfileStatus.REVOKED:
        raise ProfileRevokedError(
            f"Saved Vercel session was revoked ({profile.profile_id}). "
            "Save a new session after logging in."
        )
    if profile.status == BrowserProfileStatus.EXPIRED:
        raise ProfileExpiredError(
            "Saved Vercel session appears expired. "
            "Please open Vercel in a supervised session and save again."
        )
    if profile.status != BrowserProfileStatus.ACTIVE:
        raise ProfileNotActiveError(
            f"Saved Vercel session is not active (status={profile.status.value}). "
            "Please log in again and re-save."
        )
    if not profile.read_only_allowed:
        raise ProfileNotActiveError("Saved profile is not approved for read-only inspection.")

    storage = Path(profile.storage_path)
    if not storage.is_file():
        browser_profile_store.set_status(profile.profile_id, BrowserProfileStatus.EXPIRED)
        raise ProfileExpiredError(
            "Saved browser profile data is missing on disk. Please log in again and re-save."
        )

    return profile


def preflight_readonly_profile(profile_id: str) -> BrowserProfile:
    """Validate profile state, then browser runtime (error precedence)."""
    profile = preflight_readonly_profile_auth(profile_id)
    validate_browser_runtime_for_execution()
    return profile
