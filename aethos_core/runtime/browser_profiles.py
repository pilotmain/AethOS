# SPDX-License-Identifier: Apache-2.0
"""Browser profile model — opt-in session persistence, no passwords."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4


class BrowserProfileStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


class PersistenceMode(str, Enum):
    USE_ONCE = "use_once"
    PERSISTENT = "persistent"
    EXPIRES_7D = "expires_7d"
    EXPIRES_30D = "expires_30d"


PERSISTENCE_MODE_LABELS = {
    PersistenceMode.USE_ONCE: "Use once only",
    PersistenceMode.PERSISTENT: "Save until I remove it",
    PersistenceMode.EXPIRES_7D: "Save for 7 days",
    PersistenceMode.EXPIRES_30D: "Save for 30 days",
}


def is_profile_reusable_for_inspection(profile: "BrowserProfile") -> bool:
    if profile.status != BrowserProfileStatus.ACTIVE:
        return False
    if profile.is_time_expired():
        return False
    if profile.persistence_mode == PersistenceMode.USE_ONCE.value:
        return False
    if not Path(profile.storage_path).is_file():
        return False
    return True


def authorization_status_for_profile(profile: "BrowserProfile") -> str:
    """Saved authorization state — independent of browser runtime health."""
    if profile.status == BrowserProfileStatus.REVOKED:
        return "revoked"
    if profile.status == BrowserProfileStatus.EXPIRED or profile.is_time_expired():
        return "expired"
    if profile.status == BrowserProfileStatus.ACTIVE:
        if not Path(profile.storage_path).is_file():
            return "expired"
        return "saved"
    return "unknown"


def profile_auth_snapshot(profile: "BrowserProfile") -> dict[str, Any]:
    storage_exists = Path(profile.storage_path).is_file()
    return {
        "profile_id": profile.profile_id,
        "site": profile.site,
        "permission_mode": profile.persistence_mode,
        "authorization_status": authorization_status_for_profile(profile),
        "last_validated_at": profile.last_used_at,
        "expires_at": profile.expires_at,
        "storage_state_exists": storage_exists,
        "reusable_for_inspection": is_profile_reusable_for_inspection(profile)
        if storage_exists
        else False,
    }


def expires_at_for_mode(mode: PersistenceMode, *, now: float | None = None) -> float | None:
    from time import time

    t = now if now is not None else time()
    if mode == PersistenceMode.PERSISTENT:
        return None
    if mode == PersistenceMode.EXPIRES_7D:
        return t + 7 * 86400
    if mode == PersistenceMode.EXPIRES_30D:
        return t + 30 * 86400
    return t + 3600


def normalize_site(site: str) -> str:
    raw = (site or "").strip().lower()
    raw = raw.removeprefix("https://").removeprefix("http://")
    raw = raw.split("/")[0].split(":")[0]
    if raw.startswith("www."):
        raw = raw[4:]
    return raw or "unknown"


def scope_for_site(site: str) -> str:
    s = normalize_site(site)
    if "vercel" in s:
        return "vercel"
    return s


def _new_profile_id() -> str:
    return f"bprof-{uuid4().hex[:12]}"


@dataclass
class BrowserProfile:
    profile_id: str
    site: str
    scope: str
    storage_path: str
    created_at: float = field(default_factory=time)
    last_used_at: float | None = None
    user_approved_persistence: bool = True
    status: BrowserProfileStatus = BrowserProfileStatus.ACTIVE
    read_only_allowed: bool = True
    write_actions_allowed: bool = False
    source_session_id: str | None = None
    persistence_mode: str = PersistenceMode.PERSISTENT.value
    expires_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "site": self.site,
            "scope": self.scope,
            "storage_path": self.storage_path,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "user_approved_persistence": self.user_approved_persistence,
            "status": self.status.value,
            "read_only_allowed": self.read_only_allowed,
            "write_actions_allowed": self.write_actions_allowed,
            "source_session_id": self.source_session_id,
            "persistence_mode": self.persistence_mode,
            "expires_at": self.expires_at,
        }

    @property
    def session_type(self) -> str:
        if self.persistence_mode == PersistenceMode.USE_ONCE.value:
            return "temporary"
        return "persistent"

    def expires_label(self) -> str:
        if self.persistence_mode == PersistenceMode.PERSISTENT.value:
            return "until revoked"
        if self.persistence_mode == PersistenceMode.USE_ONCE.value:
            return "short-lived (use once)"
        if self.expires_at:
            from datetime import datetime

            return datetime.fromtimestamp(self.expires_at).strftime("%Y-%m-%d %H:%M")
        return "unknown"

    def is_time_expired(self, *, now: float | None = None) -> bool:
        if self.expires_at is None:
            return False
        from time import time

        return (now if now is not None else time()) >= self.expires_at

    def to_public_dict(self) -> dict[str, Any]:
        """Mission Control safe view — never expose storage path contents."""
        d = self.to_dict()
        d["storage_path"] = "(local profile data — not shown)"
        d["session_type"] = self.session_type
        d["expires_label"] = self.expires_label()
        d.update(profile_auth_snapshot(self))
        return d
