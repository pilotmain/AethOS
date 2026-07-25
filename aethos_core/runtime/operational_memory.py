# SPDX-License-Identifier: Apache-2.0
"""Operator-visible operational memory — confirmed entities only."""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from time import time
from typing import Any

from aethos_core.config import get_settings


def _memory_root() -> Path:
    raw = Path(get_settings().browser_profiles_dir).parent / "operational_memory"
    if not raw.is_absolute():
        repo_root = Path(__file__).resolve().parents[2]
        raw = repo_root / raw
    root = raw.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _vercel_path() -> Path:
    return _memory_root() / "vercel_projects.json"


def _railway_path() -> Path:
    return _memory_root() / "railway_services.json"


def _github_path() -> Path:
    return _memory_root() / "github_repos.json"


_NOT_PROJECT_RX = re.compile(
    r"\b([\w][\w-]*)\s+is\s+not\s+(?:an?\s+)?(?:project|app)\b",
    re.I,
)
_IS_PROJECT_RX = re.compile(
    r"\b([\w][\w-]*)\s+is\s+(?:a\s+)?(?:real\s+)?project\b",
    re.I,
)
_CONFIRM_PROJECTS_RX = re.compile(
    r"\b(?:yes|confirm)\b.*\b(?:these|my)\b.*\b(?:project|apps?)\b|"
    r"\b(?:these are all|all)\s+(?:real|my)\s+projects\b|"
    r"\byes\s+these\s+are\s+my\s+vercel\s+projects\b",
    re.I,
)
_ARCHIVED_RX = re.compile(
    r"\b([\w][\w-]*)\s+is\s+archived\b",
    re.I,
)
_MULTI_CONFIRM_RX = re.compile(
    r"\b((?:[\w-]+\s+and\s+)+[\w-]+|\w[\w-]*(?:\s*,\s*\w[\w-]*)+)\s+are\s+real\s+projects\b",
    re.I,
)


def _project_entry_from_object(
    p: Any,
    *,
    existing: dict[str, Any] | None,
    profile_id: str | None,
    last_inventory_job_id: str | None,
) -> dict[str, Any]:
    from aethos_core.browser.platforms.vercel.vercel_health_classifier import (
        apply_deployment_semantics,
        collect_health_evidence,
    )

    if hasattr(p, "production_url") and hasattr(p, "health"):
        pre_state = getattr(p, "latest_deployment_state", None)
        pre_scope = getattr(p, "latest_deployment_scope", None)
        pre_ph = getattr(p, "production_health", None)
        pre_evidence = list(getattr(p, "evidence", None) or [])
        apply_deployment_semantics(p)
        if pre_state and pre_state != "unknown":
            p.latest_deployment_state = pre_state
        if pre_scope and pre_scope != "unknown":
            p.latest_deployment_scope = pre_scope
        if pre_ph and pre_ph != "unknown":
            p.production_health = pre_ph
        if pre_evidence:
            p.evidence = pre_evidence
        elif not getattr(p, "evidence", None):
            p.evidence = collect_health_evidence(p)

    key_name = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else None)
    prior = dict(existing or {})
    health_val = (
        p.health.value
        if hasattr(p, "health") and hasattr(p.health, "value")
        else str(getattr(p, "health", prior.get("last_health") or "unknown"))
    )

    entry: dict[str, Any] = {
        "name": str(key_name or prior.get("name") or "").lower(),
        "confirmed": True,
        "confirmed_by_user": bool(prior.get("confirmed_by_user", False)),
        "archived": bool(prior.get("archived", False)),
        "ignored_as_project": bool(prior.get("ignored_as_project", False)),
        "last_seen_at": time(),
        "last_profile_id": profile_id or prior.get("last_profile_id"),
        "last_inventory_job_id": last_inventory_job_id or prior.get("last_inventory_job_id"),
        "confidence": prior.get("confidence") or "high",
        "last_health": health_val,
        "health_confidence": getattr(p, "health_confidence", None) or prior.get("health_confidence") or health_val,
        "production_health": getattr(p, "production_health", None) or prior.get("production_health") or "unknown",
        "latest_deployment_state": getattr(p, "latest_deployment_state", None)
        or prior.get("latest_deployment_state")
        or "unknown",
        "latest_deployment_scope": getattr(p, "latest_deployment_scope", None)
        or prior.get("latest_deployment_scope")
        or "unknown",
        "operator_status": getattr(p, "operator_status", None) or prior.get("operator_status") or "unknown",
        "url_type": getattr(p, "url_type", None) or prior.get("url_type") or "unknown",
        "production_url": getattr(p, "production_url", None) or prior.get("production_url"),
        "production_url_source": getattr(p, "production_url_source", None) or prior.get("production_url_source"),
        "known_production_url": getattr(p, "production_url", None) or prior.get("known_production_url"),
        "known_repo": getattr(p, "git_repo", None) or prior.get("known_repo"),
        "attention_reason": getattr(p, "attention_reason", None) or prior.get("attention_reason"),
        "evidence": list(getattr(p, "evidence", None) or prior.get("evidence") or []),
    }
    if getattr(p, "known_domains", None):
        entry["known_domains"] = list(p.known_domains)
    elif prior.get("known_domains"):
        entry["known_domains"] = list(prior["known_domains"])
    if getattr(p, "environment", None):
        entry["environment"] = p.environment
    if health_val in ("healthy", "likely_healthy"):
        entry["last_seen_healthy"] = time()
    return entry


class OperationalMemoryStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()

    def _load(self) -> dict[str, Any]:
        path = _vercel_path()
        if not path.is_file():
            return {
                "platforms": {
                    "vercel": {
                        "confirmed_projects": {},
                        "ignored_labels": {},
                        "updated_at": None,
                    }
                }
            }
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {
                "platforms": {
                    "vercel": {
                        "confirmed_projects": {},
                        "ignored_labels": {},
                        "updated_at": None,
                    }
                }
            }

    def _save(self, data: dict[str, Any]) -> None:
        _vercel_path().write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _vercel_bucket(self, data: dict[str, Any]) -> dict[str, Any]:
        return data.setdefault("platforms", {}).setdefault("vercel", {})

    def _railway_bucket(self, data: dict[str, Any]) -> dict[str, Any]:
        return data.setdefault("platforms", {}).setdefault("railway", {})

    def _github_bucket(self, data: dict[str, Any]) -> dict[str, Any]:
        return data.setdefault("platforms", {}).setdefault("github", {})

    def _load_platform_file(self, path: Path, platform: str) -> dict[str, Any]:
        empty = {"platforms": {platform: {"confirmed_entities": {}, "updated_at": None}}}
        if not path.is_file():
            return empty
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return empty

    def _save_platform_file(self, path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def record_vercel_extraction(
        self,
        artifact: Any,
        *,
        profile_id: str | None = None,
        last_inventory_job_id: str | None = None,
    ) -> list[str]:
        """Persist full structured project state from inventory artifact."""
        with self._lock:
            data = self._load()
            bucket = self._vercel_bucket(data)
            confirmed: dict[str, Any] = bucket.setdefault("confirmed_projects", {})
            ignored_store: dict[str, Any] = bucket.setdefault("ignored_labels", {})

            for p in getattr(artifact, "projects", []) or []:
                name = getattr(p, "name", None) or (p.get("name") if isinstance(p, dict) else None)
                if not name:
                    continue
                key = str(name).lower()
                if key in ignored_store:
                    continue
                prior = confirmed.get(key, {})
                if prior.get("ignored_as_project"):
                    continue
                entry = _project_entry_from_object(
                    p,
                    existing=prior,
                    profile_id=profile_id,
                    last_inventory_job_id=last_inventory_job_id,
                )
                if prior.get("confirmed_by_user"):
                    entry["confirmed_by_user"] = True
                    entry["confidence"] = "high"
                confirmed[key] = entry

            for label in getattr(artifact, "ignored_labels", []) or []:
                key = str(label).lower()
                ignored_store[key] = {
                    "name": key,
                    "last_seen_at": time(),
                    "reason": "low_confidence_extraction",
                    "ignored_as_project": True,
                }
                confirmed.pop(key, None)

            if last_inventory_job_id:
                bucket["last_inventory_job_id"] = last_inventory_job_id
            bucket["updated_at"] = time()
            self._save(data)
            return sorted(confirmed.keys())

    def record_vercel_api_execution(
        self,
        *,
        project_name: str,
        operation_type: str,
        payload: dict[str, Any],
    ) -> None:
        """Enrich operational memory from API-backed readonly execution."""
        key = str(project_name or "").strip().lower()
        if not key:
            return
        with self._lock:
            data = self._load()
            bucket = self._vercel_bucket(data)
            confirmed: dict[str, Any] = bucket.setdefault("confirmed_projects", {})
            prior = dict(confirmed.get(key, {"name": key, "confirmed": True}))
            prior["last_seen_at"] = time()
            prior["last_api_execution_at"] = time()
            prior["last_api_operation"] = operation_type

            if operation_type in ("list_deployments", "why_down", "inspect_failed_deployment", "check_logs"):
                deps = payload.get("deployments") or []
                if deps:
                    latest = deps[0] if isinstance(deps[0], dict) else {}
                    prior["latest_deployment_state"] = str(latest.get("state") or prior.get("latest_deployment_state") or "unknown")
                    prior["latest_deployment_scope"] = str(latest.get("target") or prior.get("latest_deployment_scope") or "unknown")
                    if latest.get("state") == "error":
                        prior["latest_failure_reason"] = str(latest.get("error_message") or "")[:500]
                        prior["latest_failed_deploy_at"] = latest.get("created_at")
                    elif latest.get("state") in ("ready", "completed"):
                        prior["latest_successful_deploy_at"] = latest.get("ready_at") or latest.get("created_at")
                    prior["known_repo"] = prior.get("known_repo") or latest.get("branch")

            if operation_type == "list_domains":
                domains = [str(d.get("domain") or "") for d in payload.get("domains") or [] if isinstance(d, dict)]
                if domains:
                    prior["known_domains"] = sorted(set(domains))

            if operation_type == "project_details":
                details = payload.get("details") or {}
                if isinstance(details, dict):
                    if details.get("repo_link"):
                        prior["known_repo"] = details.get("repo_link")
                    if details.get("framework"):
                        prior["known_framework"] = details.get("framework")
                    if details.get("production_branch"):
                        prior["production_branch"] = details.get("production_branch")
                    if details.get("production_url"):
                        prior["production_url"] = details.get("production_url")

            confirmed[key] = prior
            bucket["updated_at"] = time()
            self._save(data)

    def record_railway_inventory(
        self,
        services: list[dict[str, Any]],
        *,
        last_inventory_job_id: str | None = None,
    ) -> list[str]:
        """Persist Railway service names from readonly inventory (Phase 9.3L parity)."""
        with self._lock:
            data = self._load_platform_file(_railway_path(), "railway")
            bucket = self._railway_bucket(data)
            confirmed: dict[str, Any] = bucket.setdefault("confirmed_entities", {})
            for row in services or []:
                name = str(row.get("name") or row.get("service_name") or "").strip().lower()
                if not name:
                    continue
                prior = dict(confirmed.get(name, {}))
                prior.update(
                    {
                        "name": name,
                        "confirmed": True,
                        "service_name": name,
                        "project_name": row.get("project_name"),
                        "environment": row.get("environment") or "production",
                        "service_id": row.get("service_id"),
                        "last_seen_at": time(),
                        "last_inventory_job_id": last_inventory_job_id or prior.get("last_inventory_job_id"),
                        "confidence": "high",
                    }
                )
                confirmed[name] = prior
            if last_inventory_job_id:
                bucket["last_inventory_job_id"] = last_inventory_job_id
            bucket["updated_at"] = time()
            self._save_platform_file(_railway_path(), data)
            return sorted(confirmed.keys())

    def known_railway_services(self) -> list[str]:
        with self._lock:
            bucket = self._railway_bucket(self._load_platform_file(_railway_path(), "railway"))
            return sorted(
                k
                for k, v in bucket.get("confirmed_entities", {}).items()
                if not v.get("ignored_as_entity")
            )

    def get_railway_service_memory(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            bucket = self._railway_bucket(self._load_platform_file(_railway_path(), "railway"))
            raw = bucket.get("confirmed_entities", {})
            return {k: dict(v) for k, v in raw.items() if not v.get("ignored_as_entity")}

    def record_github_inventory(
        self,
        repos: list[dict[str, Any]],
        *,
        last_inventory_job_id: str | None = None,
    ) -> list[str]:
        """Persist GitHub repo names from readonly inventory (Phase 9.3L parity)."""
        with self._lock:
            data = self._load_platform_file(_github_path(), "github")
            bucket = self._github_bucket(data)
            confirmed: dict[str, Any] = bucket.setdefault("confirmed_entities", {})
            for row in repos or []:
                name = str(row.get("full_name") or row.get("name") or "").strip().lower()
                if not name:
                    continue
                prior = dict(confirmed.get(name, {}))
                prior.update(
                    {
                        "name": name,
                        "confirmed": True,
                        "full_name": name,
                        "html_url": row.get("html_url"),
                        "last_seen_at": time(),
                        "last_inventory_job_id": last_inventory_job_id or prior.get("last_inventory_job_id"),
                        "confidence": "high",
                    }
                )
                confirmed[name] = prior
            if last_inventory_job_id:
                bucket["last_inventory_job_id"] = last_inventory_job_id
            bucket["updated_at"] = time()
            self._save_platform_file(_github_path(), data)
            return sorted(confirmed.keys())

    def known_github_repos(self) -> list[str]:
        with self._lock:
            bucket = self._github_bucket(self._load_platform_file(_github_path(), "github"))
            return sorted(
                k
                for k, v in bucket.get("confirmed_entities", {}).items()
                if not v.get("ignored_as_entity")
            )

    def get_github_repo_memory(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            bucket = self._github_bucket(self._load_platform_file(_github_path(), "github"))
            raw = bucket.get("confirmed_entities", {})
            return {k: dict(v) for k, v in raw.items() if not v.get("ignored_as_entity")}

    def known_vercel_projects(self) -> list[str]:
        with self._lock:
            bucket = self._vercel_bucket(self._load())
            out: list[str] = []
            for k, v in bucket.get("confirmed_projects", {}).items():
                if v.get("ignored_as_project") or v.get("archived"):
                    continue
                out.append(k)
            return sorted(out)

    def get_vercel_project_memory(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            bucket = self._vercel_bucket(self._load())
            raw = bucket.get("confirmed_projects", {})
            return {k: dict(v) for k, v in raw.items() if not v.get("ignored_as_project")}

    def confirm_likely_projects(self, names: list[str]) -> list[str]:
        with self._lock:
            data = self._load()
            bucket = self._vercel_bucket(data)
            confirmed: dict[str, Any] = bucket.setdefault("confirmed_projects", {})
            for raw in names:
                key = str(raw).strip().lower()
                if not key:
                    continue
                prior = confirmed.get(key, {})
                prior.update(
                    {
                        "name": key,
                        "confirmed": True,
                        "confirmed_by_user": True,
                        "updated_at": time(),
                    }
                )
                confirmed[key] = prior
                bucket.get("ignored_labels", {}).pop(key, None)
            bucket["updated_at"] = time()
            self._save(data)
            return sorted(confirmed.keys())

    def _mark_project(self, name: str, **fields: Any) -> None:
        with self._lock:
            data = self._load()
            bucket = self._vercel_bucket(data)
            confirmed: dict[str, Any] = bucket.setdefault("confirmed_projects", {})
            key = name.lower()
            prior = confirmed.get(key, {"name": key})
            prior.update(fields)
            prior["updated_at"] = time()
            confirmed[key] = prior
            bucket["updated_at"] = time()
            self._save(data)

    def apply_user_correction(self, text: str) -> tuple[str, bool]:
        """Parse simple corrections; returns (reply, applied)."""
        raw = (text or "").strip()

        m_archived = _ARCHIVED_RX.search(raw)
        if m_archived:
            name = m_archived.group(1).lower()
            self._mark_project(name, archived=True, confirmed=True)
            return f"Got it — I'll treat `{name}` as archived and exclude it from active operations.", True

        m_not = _NOT_PROJECT_RX.search(raw)
        if m_not:
            name = m_not.group(1).lower()
            with self._lock:
                data = self._load()
                bucket = self._vercel_bucket(data)
                bucket.setdefault("ignored_labels", {})[name] = {
                    "name": name,
                    "ignored_by_user": True,
                    "ignored_as_project": True,
                    "updated_at": time(),
                }
                proj = bucket.get("confirmed_projects", {}).get(name, {})
                if proj:
                    proj["ignored_as_project"] = True
                    bucket["confirmed_projects"][name] = proj
                else:
                    bucket.get("confirmed_projects", {}).pop(name, None)
                bucket["updated_at"] = time()
                self._save(data)
            return f"Got it — I will ignore `{name}` as a Vercel project label going forward.", True

        m_multi = _MULTI_CONFIRM_RX.search(raw)
        if m_multi:
            chunk = m_multi.group(1)
            names = re.split(r"\s+and\s+|,\s*", chunk)
            cleaned = [n.strip().lower() for n in names if n.strip()]
            if cleaned:
                self.confirm_likely_projects(cleaned)
                preview = ", ".join(f"`{n}`" for n in cleaned[:8])
                return f"Got it — I'll treat these as confirmed Vercel projects: {preview}.", True

        if _CONFIRM_PROJECTS_RX.search(raw):
            with self._lock:
                bucket = self._vercel_bucket(self._load())
                likely = [
                    k
                    for k, v in bucket.get("confirmed_projects", {}).items()
                    if not v.get("confirmed_by_user") and not v.get("ignored_as_project")
                ]
            if likely:
                self.confirm_likely_projects(likely)
                preview = ", ".join(f"`{n}`" for n in likely[:8])
                extra = f" (+{len(likely) - 8} more)" if len(likely) > 8 else ""
                return (
                    f"Got it — I'll treat these as confirmed Vercel projects: {preview}{extra}.",
                    True,
                )
            return (
                "Got it — I'll treat likely project names as confirmed when I see them on the next inspection.",
                True,
            )

        m_yes = _IS_PROJECT_RX.search(raw)
        if m_yes:
            name = m_yes.group(1).lower()
            self._mark_project(name, confirmed=True, confirmed_by_user=True)
            with self._lock:
                data = self._load()
                self._vercel_bucket(data).get("ignored_labels", {}).pop(name, None)
                self._save(data)
            return f"Got it — I'll treat `{name}` as a real Vercel project in future summaries.", True

        return "", False

    def clear_for_tests(self) -> None:
        with self._lock:
            root = _memory_root()
            for path in (_vercel_path(), _railway_path(), _github_path()):
                if path.is_file():
                    path.unlink()
            for extra in root.glob("*.json"):
                extra.unlink(missing_ok=True)


operational_memory = OperationalMemoryStore()


def compute_vercel_memory_delta(
    extracted_names: list[str],
    known_before: list[str],
) -> dict[str, list[str]]:
    ext = {str(n).strip().lower() for n in extracted_names if str(n).strip()}
    known = {str(n).strip().lower() for n in known_before if str(n).strip()}
    return {
        "confirmed_this_run": sorted(ext & known),
        "newly_detected_this_run": sorted(ext - known),
        "known_not_visible": sorted(known - ext),
    }


def record_vercel_projects(projects, *, profile_id=None, last_inventory_job_id=None):
    class _Wrap:
        def __init__(self, projects, ignored=None):
            self.projects = projects
            self.ignored_labels = ignored or []

    return operational_memory.record_vercel_extraction(
        _Wrap(projects),
        profile_id=profile_id,
        last_inventory_job_id=last_inventory_job_id,
    )
