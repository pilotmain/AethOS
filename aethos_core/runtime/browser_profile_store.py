# SPDX-License-Identifier: Apache-2.0
"""Persistent browser profile registry — JSON metadata + Playwright storage state files."""

from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path
from time import time
from typing import Any

from aethos_core.config import get_settings
from aethos_core.runtime.browser_profiles import (
    BrowserProfile,
    BrowserProfileStatus,
    PersistenceMode,
    _new_profile_id,
    expires_at_for_mode,
    normalize_site,
    scope_for_site,
)


def profiles_root_path() -> Path:
    """Stable absolute path — same for save, list, and inspector regardless of process cwd."""
    raw = Path(get_settings().browser_profiles_dir)
    if raw.is_absolute():
        root = raw
    else:
        # aethos_core/runtime/browser_profile_store.py → repo root
        repo_root = Path(__file__).resolve().parents[2]
        root = repo_root / raw
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _profiles_root() -> Path:
    return profiles_root_path()


def store_diagnostics() -> dict[str, Any]:
    root = profiles_root_path()
    profiles = []
    for meta in root.glob("bprof-*.json"):
        if meta.name.endswith(".storage.json"):
            continue
        storage = root / f"{meta.stem}.storage.json"
        profiles.append(
            {
                "profile_id": meta.stem,
                "meta_exists": meta.is_file(),
                "storage_exists": storage.is_file(),
            }
        )
    return {
        "profile_store_path": str(root),
        "profile_count": len(profiles),
        "profiles": profiles,
    }


def _meta_path(profile_id: str) -> Path:
    return _profiles_root() / f"{profile_id}.json"


def _storage_path(profile_id: str) -> Path:
    return _profiles_root() / f"{profile_id}.storage.json"


class BrowserProfileStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cache: dict[str, BrowserProfile] = {}

    def _load_meta(self, profile_id: str) -> BrowserProfile | None:
        path = _meta_path(profile_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        status_raw = data.get("status", BrowserProfileStatus.ACTIVE.value)
        try:
            status = BrowserProfileStatus(status_raw)
        except ValueError:
            status = BrowserProfileStatus.UNKNOWN
        mode_raw = data.get("persistence_mode") or PersistenceMode.PERSISTENT.value
        try:
            PersistenceMode(mode_raw)
        except ValueError:
            mode_raw = PersistenceMode.PERSISTENT.value
        profile = BrowserProfile(
            profile_id=data["profile_id"],
            site=data.get("site", "unknown"),
            scope=data.get("scope", "unknown"),
            storage_path=str(data.get("storage_path") or _storage_path(profile_id)),
            created_at=float(data.get("created_at") or time()),
            last_used_at=data.get("last_used_at"),
            user_approved_persistence=bool(data.get("user_approved_persistence", True)),
            status=status,
            read_only_allowed=bool(data.get("read_only_allowed", True)),
            write_actions_allowed=bool(data.get("write_actions_allowed", False)),
            source_session_id=data.get("source_session_id"),
            persistence_mode=mode_raw,
            expires_at=data.get("expires_at"),
        )
        if profile.status == BrowserProfileStatus.ACTIVE and profile.is_time_expired():
            profile.status = BrowserProfileStatus.EXPIRED
            self._save_meta(profile)
        return profile

    def _atomic_write_json(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        data = json.dumps(payload, indent=2)
        tmp.write_text(data, encoding="utf-8")
        tmp.replace(path)

    def _save_meta(self, profile: BrowserProfile) -> None:
        path = _meta_path(profile.profile_id)
        self._atomic_write_json(path, profile.to_dict())

    def find_by_source_session(self, session_id: str) -> BrowserProfile | None:
        with self._lock:
            for p in self._list_unlocked():
                if p.source_session_id == session_id and p.status == BrowserProfileStatus.ACTIVE:
                    return p
        return None

    def _list_unlocked(self) -> list[BrowserProfile]:
        profiles: list[BrowserProfile] = []
        for meta in _profiles_root().glob("bprof-*.json"):
            if meta.name.endswith(".storage.json"):
                continue
            p = self._load_meta(meta.stem)
            if p:
                profiles.append(p)
                self._cache[p.profile_id] = p
        profiles.sort(key=lambda p: p.created_at, reverse=True)
        return profiles

    def list_all(self, *, refresh: bool = True) -> list[BrowserProfile]:
        with self._lock:
            if refresh:
                self._cache.clear()
            return self._list_unlocked()

    def get(self, profile_id: str) -> BrowserProfile | None:
        with self._lock:
            p = self._load_meta(profile_id)
            if p:
                self._cache[profile_id] = p
            else:
                self._cache.pop(profile_id, None)
            return p

    def find_active_for_site(self, site: str) -> BrowserProfile | None:
        from aethos_core.runtime.browser_profiles import is_profile_reusable_for_inspection

        norm = normalize_site(site)
        for p in self.list_all():
            if not is_profile_reusable_for_inspection(p):
                continue
            if normalize_site(p.site) == norm and p.read_only_allowed:
                return p
        return None

    def find_active_for_scope(self, scope: str) -> BrowserProfile | None:
        from aethos_core.runtime.browser_profiles import is_profile_reusable_for_inspection

        for p in self.list_all():
            if not is_profile_reusable_for_inspection(p):
                continue
            if p.scope == scope and p.read_only_allowed:
                return p
        return None

    def save_from_session(
        self,
        *,
        session_id: str,
        site: str,
        storage_state: dict[str, Any],
        persistence_mode: str = PersistenceMode.USE_ONCE.value,
    ) -> BrowserProfile:
        """Create profile after explicit user opt-in — replaces prior profile for same site."""
        norm_site = normalize_site(site)
        scope = scope_for_site(norm_site)
        with self._lock:
            for existing in self._list_unlocked():
                if normalize_site(existing.site) == norm_site and existing.status == BrowserProfileStatus.ACTIVE:
                    self._forget_unlocked(existing.profile_id)
            for existing in self._list_unlocked():
                if existing.source_session_id == session_id and existing.status == BrowserProfileStatus.ACTIVE:
                    return existing

            profile_id = _new_profile_id()
            storage_file = _storage_path(profile_id)
            self._atomic_write_json(storage_file, storage_state)
            try:
                mode = PersistenceMode(persistence_mode)
            except ValueError:
                mode = PersistenceMode.USE_ONCE
            profile = BrowserProfile(
                profile_id=profile_id,
                site=norm_site,
                scope=scope,
                storage_path=str(storage_file),
                user_approved_persistence=mode != PersistenceMode.USE_ONCE,
                status=BrowserProfileStatus.ACTIVE,
                source_session_id=session_id,
                persistence_mode=mode.value,
                expires_at=expires_at_for_mode(mode),
            )
            self._save_meta(profile)
            self._verify_persisted(profile)
            self._cache[profile_id] = profile
            return profile

    def _verify_persisted(self, profile: BrowserProfile) -> None:
        if not _meta_path(profile.profile_id).is_file():
            raise OSError(f"Profile metadata not written for {profile.profile_id}")
        storage = Path(profile.storage_path)
        if not storage.is_file():
            raise OSError(f"Profile storage state missing at {storage}")

    def touch_used(self, profile_id: str) -> None:
        with self._lock:
            p = self._load_meta(profile_id)
            if not p:
                return
            p.last_used_at = time()
            self._save_meta(p)
            self._cache[profile_id] = p

    def set_status(self, profile_id: str, status: BrowserProfileStatus) -> BrowserProfile | None:
        with self._lock:
            p = self._load_meta(profile_id)
            if not p:
                return None
            p.status = status
            self._save_meta(p)
            self._cache[profile_id] = p
            return p

    def _forget_unlocked(self, profile_id: str) -> bool:
        p = self._cache.get(profile_id) or self._load_meta(profile_id)
        if not p:
            return False
        try:
            Path(p.storage_path).unlink(missing_ok=True)
        except OSError:
            pass
        _meta_path(profile_id).unlink(missing_ok=True)
        self._cache.pop(profile_id, None)
        return True

    def forget(self, profile_id: str) -> bool:
        with self._lock:
            return self._forget_unlocked(profile_id)

    def clear_all_for_tests(self) -> None:
        with self._lock:
            root = _profiles_root()
            if root.is_dir():
                shutil.rmtree(root, ignore_errors=True)
            root.mkdir(parents=True, exist_ok=True)
            self._cache.clear()


browser_profile_store = BrowserProfileStore()

_last_loaded_from_disk_at: float | None = None


def load_profiles_from_disk_at_startup() -> dict[str, Any]:
    """Refresh profile registry from disk — call during API startup."""
    global _last_loaded_from_disk_at
    from time import time

    profiles = browser_profile_store.list_all(refresh=True)
    _last_loaded_from_disk_at = time()
    diag = store_diagnostics()
    persistent = sum(
        1
        for p in profiles
        if p.persistence_mode != "use_once" and p.status.value == "active"
    )
    temporary = sum(1 for p in profiles if p.persistence_mode == "use_once")
    expired = sum(1 for p in profiles if p.status.value == "expired")
    return {
        **diag,
        "loaded_at": _last_loaded_from_disk_at,
        "persistent_profiles": persistent,
        "temporary_profiles": temporary,
        "expired_profiles": expired,
        "profile_ids": [p.profile_id for p in profiles],
    }


def profile_store_startup_info() -> dict[str, Any]:
    diag = store_diagnostics()
    return {
        **diag,
        "last_loaded_from_disk_at": _last_loaded_from_disk_at,
    }

