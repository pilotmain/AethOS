# SPDX-License-Identifier: Apache-2.0
"""Commit and repository identity normalization."""

from __future__ import annotations


def normalize_commit_sha(sha: str) -> str:
    return (sha or "").strip().lower()


def commit_prefix(sha: str, *, length: int = 7) -> str:
    normalized = normalize_commit_sha(sha)
    return normalized[:length] if normalized else ""


def commits_match(left: str, right: str) -> bool:
    a = normalize_commit_sha(left)
    b = normalize_commit_sha(right)
    if not a or not b:
        return False
    shorter = min(len(a), len(b), 12)
    return a[:shorter] == b[:shorter]


def normalize_repo(repo: str) -> str:
    raw = (repo or "").strip().lower()
    if not raw:
        return ""
    if "/" not in raw:
        return raw
    owner, name = raw.split("/", 1)
    return f"{owner.strip()}/{name.strip()}"


def repos_match(left: str, right: str) -> bool:
    a = normalize_repo(left)
    b = normalize_repo(right)
    if not a or not b:
        return False
    if a == b:
        return True
    return a.split("/")[-1] == b.split("/")[-1]


def normalize_branch(branch: str) -> str:
    return (branch or "").strip().lower()
