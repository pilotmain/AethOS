#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""§10 AethOS backup / restore for governed state.

Creates and restores a compressed archive of the critical data directories — the
credential vault, the auth store, the audit ledger, deployment-target registry,
and the local-workspace registry. The archive is self-contained and can be
restored into a clean instance.

Data-residency note: AethOS stores all governed state on the local filesystem
under ``data/`` (or the configured dirs). Backups are written wherever you point
them; for regulated workloads, target an encrypted volume in your required
region. Secrets in the vault remain encrypted at rest inside the archive.

Usage:
    python scripts/aethos_backup.py backup [--out data/backups]
    python scripts/aethos_backup.py restore <archive.tar.gz> [--dest .] [--force]
"""

from __future__ import annotations

import argparse
import sys
import tarfile
import time
from pathlib import Path

# Critical state, relative to the repo/instance root.
BACKUP_PATHS = (
    "data/credentials",
    "data/secrets",
    "data/auth",
    "data/audit",
    "data/deployment_targets",
    "data/local_workspace",
    "data/operator_persona",
)


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def do_backup(out_dir: str) -> Path:
    root = _root()
    dest = Path(out_dir)
    if not dest.is_absolute():
        dest = root / dest
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / f"aethos-backup-{time.strftime('%Y%m%dT%H%M%S')}.tar.gz"
    included = 0
    with tarfile.open(archive, "w:gz") as tar:
        for rel in BACKUP_PATHS:
            path = root / rel
            if path.exists():
                tar.add(path, arcname=rel)
                included += 1
    print(f"backup: wrote {archive} ({included} paths)")
    return archive


def do_restore(archive: str, dest: str, force: bool) -> None:
    archive_path = Path(archive)
    if not archive_path.is_file():
        sys.exit(f"restore: archive not found: {archive}")
    target = Path(dest)
    if not target.is_absolute():
        target = _root() / dest
    for rel in BACKUP_PATHS:
        existing = target / rel
        if existing.exists() and not force:
            sys.exit(f"restore: {existing} exists; use --force to overwrite")
    with tarfile.open(archive_path, "r:gz") as tar:
        # Guard against path traversal in untrusted archives.
        for member in tar.getmembers():
            member_path = (target / member.name).resolve()
            if not str(member_path).startswith(str(target.resolve())):
                sys.exit(f"restore: unsafe path in archive: {member.name}")
        tar.extractall(target)
    print(f"restore: extracted {archive} into {target}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AethOS backup / restore")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup", help="create a backup archive")
    b.add_argument("--out", default="data/backups")
    r = sub.add_parser("restore", help="restore from a backup archive")
    r.add_argument("archive")
    r.add_argument("--dest", default=".")
    r.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "backup":
        do_backup(args.out)
    elif args.cmd == "restore":
        do_restore(args.archive, args.dest, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
