# SPDX-License-Identifier: Apache-2.0
"""Extract GitHub repository references from user text."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_GITHUB_URL_RX = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([a-z0-9][a-z0-9._-]*)/([a-z0-9][a-z0-9._-]*)/?",
    re.I,
)
_OWNER_REPO_RX = re.compile(
    r"\b([a-z0-9][a-z0-9._-]*)/([a-z0-9][a-z0-9._-]*)\b",
    re.I,
)
_REPO_PREFIX_RX = re.compile(r"\b(?:repo|repository)\s+([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*)\b", re.I)
_USE_REPO_RX = re.compile(
    r"\b(?:use|switch\s+to|try)\s+([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*)\b",
    re.I,
)
_RAILWAY_RESTART_REPO_RX = re.compile(
    r"\b(?:restart|redeploy|re-?deploy)\s+(?:railway|rail\s*way)\s+([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*)\b",
    re.I,
)
_CORRECTION_CUE_RX = re.compile(r"\b(?:instead|correct\s+repo|right\s+repo|actual\s+repo|use\s+this)\b", re.I)
_SKIP_OWNERS = frozenset({"production", "staging", "development", "default"})


@dataclass
class RepoReference:
    provider: str = "github"
    owner: str = ""
    repo: str = ""
    full_name: str = ""
    confidence: float = 0.0
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "owner": self.owner,
            "repo": self.repo,
            "full_name": self.full_name,
            "confidence": self.confidence,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> RepoReference:
        owner = str(raw.get("owner") or "")
        repo = str(raw.get("repo") or "")
        full_name = str(raw.get("full_name") or f"{owner}/{repo}".strip("/"))
        if "/" in full_name and not owner:
            owner, repo = full_name.split("/", 1)
        return cls(
            provider=str(raw.get("provider") or "github"),
            owner=owner,
            repo=repo,
            full_name=full_name,
            confidence=float(raw.get("confidence") or 0.0),
            source=str(raw.get("source") or ""),
        )


def _build_ref(owner: str, repo: str, *, confidence: float, source: str) -> RepoReference:
    owner = owner.strip()
    repo = repo.strip().rstrip("/")
    full_name = f"{owner}/{repo}"
    return RepoReference(owner=owner, repo=repo, full_name=full_name, confidence=confidence, source=source)


def _valid_owner_repo(owner: str, repo: str) -> bool:
    if not owner or not repo:
        return False
    if owner.lower() in _SKIP_OWNERS:
        return False
    if repo.lower() in {"production", "staging", "development", "service"}:
        return False
    return True


def parse_repo_reference(text: str) -> RepoReference | None:
    raw = (text or "").strip()
    if not raw:
        return None

    match = _GITHUB_URL_RX.search(raw)
    if match:
        owner, repo = match.group(1), match.group(2)
        if _valid_owner_repo(owner, repo):
            return _build_ref(owner, repo, confidence=0.98, source="github_url")

    match = _RAILWAY_RESTART_REPO_RX.search(raw)
    if match:
        parts = match.group(1).split("/", 1)
        if len(parts) == 2 and _valid_owner_repo(parts[0], parts[1]):
            return _build_ref(parts[0], parts[1], confidence=0.97, source="railway_restart_repo")

    for rx, confidence, source in (
        (_REPO_PREFIX_RX, 0.92, "repo_prefix"),
        (_USE_REPO_RX, 0.9, "use_repo"),
    ):
        match = rx.search(raw)
        if match:
            parts = match.group(1).split("/", 1)
            if len(parts) == 2 and _valid_owner_repo(parts[0], parts[1]):
                return _build_ref(parts[0], parts[1], confidence=confidence, source=source)

    best: RepoReference | None = None
    for match in _OWNER_REPO_RX.finditer(raw):
        owner, repo = match.group(1), match.group(2)
        if not _valid_owner_repo(owner, repo):
            continue
        confidence = 0.85
        if _CORRECTION_CUE_RX.search(raw):
            confidence = 0.96
        if "github.com" in raw.lower():
            confidence = max(confidence, 0.95)
        candidate = _build_ref(owner, repo, confidence=confidence, source="owner_repo")
        if best is None or candidate.confidence > best.confidence:
            best = candidate
    return best


def parse_repo_references(text: str) -> list[RepoReference]:
    ref = parse_repo_reference(text)
    return [ref] if ref else []


def is_railway_restart_with_repo_target(text: str) -> bool:
    return _RAILWAY_RESTART_REPO_RX.search(text or "") is not None


def repo_matches_service_name(repo_ref: RepoReference, service_name: str) -> bool:
    svc = (service_name or "").strip().lower()
    repo = (repo_ref.repo or "").strip().lower()
    full = (repo_ref.full_name or "").strip().lower()
    if not svc or not repo:
        return False
    return repo == svc or svc in full or repo in svc or svc in repo
