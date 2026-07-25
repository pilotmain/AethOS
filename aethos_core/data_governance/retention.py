# SPDX-License-Identifier: Apache-2.0
"""§10 Data retention engine.

Prunes aged operational data per category on an opt-in basis (0 days = keep
forever, the default, so nothing is ever deleted by surprise). Chat/jobs/artifact
categories prune by file mtime; the audit category *archives* (never silently
deletes) via the ledger's hash-preserving rotation.

Designed to be invoked from a scheduler or a cron/CLI; ``prune_retention`` is
idempotent and supports a dry run that reports what *would* be removed.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

# category → data subdirectories whose files are pruned by mtime.
_CATEGORY_DIRS: dict[str, tuple[str, ...]] = {
    "chat": ("data/conversation", "data/conversation_continuity", "data/conversation_plans"),
    "jobs": ("data/agent_artifacts", "data/action_runtime"),
    "artifacts": ("data/browser_artifacts", "data/research_artifacts", "data/local_workspace_artifacts"),
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _prune_dir(directory: Path, cutoff: float, dry_run: bool) -> tuple[int, list[str]]:
    if not directory.is_dir():
        return 0, []
    removed = 0
    samples: list[str] = []
    for entry in directory.rglob("*"):
        if not entry.is_file():
            continue
        try:
            if entry.stat().st_mtime >= cutoff:
                continue
        except OSError:
            continue
        if len(samples) < 5:
            samples.append(str(entry.relative_to(_repo_root())))
        if not dry_run:
            try:
                entry.unlink()
            except OSError:
                continue
        removed += 1
    return removed, samples


def prune_retention(*, dry_run: bool = True) -> dict[str, Any]:
    from aethos_core.config import get_settings

    s = get_settings()
    report: dict[str, Any] = {"enabled": bool(s.retention_enabled), "dry_run": dry_run, "categories": {}}
    if not s.retention_enabled:
        report["note"] = "retention_disabled"
        return report

    now = time.time()
    days_by_cat = {
        "chat": s.retention_chat_days,
        "jobs": s.retention_jobs_days,
        "artifacts": s.retention_artifacts_days,
    }
    root = _repo_root()
    for category, dirs in _CATEGORY_DIRS.items():
        days = days_by_cat.get(category, 0)
        if days <= 0:
            report["categories"][category] = {"days": 0, "skipped": "keep_forever"}
            continue
        cutoff = now - days * 86400
        total = 0
        samples: list[str] = []
        for rel in dirs:
            count, sample = _prune_dir(root / rel, cutoff, dry_run)
            total += count
            samples.extend(sample)
        report["categories"][category] = {"days": days, "removed": total, "samples": samples[:5]}

    # Audit retention archives (never deletes) to preserve tamper-evidence.
    if s.retention_audit_days > 0:
        cutoff = now - s.retention_audit_days * 86400
        if dry_run:
            from aethos_core.observability.audit_ledger import read_entries

            old = [e for e in read_entries() if e.get("at", 0) < cutoff]
            report["categories"]["audit"] = {"days": s.retention_audit_days, "would_archive": len(old)}
        else:
            from aethos_core.observability.audit_ledger import archive_before

            report["categories"]["audit"] = {"days": s.retention_audit_days, **archive_before(cutoff)}
    else:
        report["categories"]["audit"] = {"days": 0, "skipped": "keep_forever"}

    return report
