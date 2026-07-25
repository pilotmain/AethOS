#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Seed FIX 187 Phase 2 expansion approvals for all multi-repo pilot targets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed FIX 187 repo expansion approvals (Phase 2 order)")
    parser.add_argument("--session-id", default="operator", help="Mission Control session id")
    args = parser.parse_args()

    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
        PHASE_2_REPOSITORY_ORDER,
    )
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
        append_independent_repository_trust_expansion_record,
        has_repo_expansion_approval,
    )

    sid = (args.session_id or "operator").strip()[:64] or "operator"
    seeded = 0
    for repository in PHASE_2_REPOSITORY_ORDER:
        if has_repo_expansion_approval(repository=repository):
            print(f"skip (already approved): {repository}")
            continue
        record, blockers = append_independent_repository_trust_expansion_record(
            session_id=sid,
            kind="repo_expansion_approval",
            content=f"Operator approves {repository} for Phase 2 multi-repo pilot program",
            repository=repository,
        )
        if blockers or not record:
            print(f"FAILED {repository}: {blockers}")
            return 1
        print(f"Seeded FIX 187 expansion: {repository} → {record.get('record_id')}")
        seeded += 1

    print(f"Done — {seeded} new approval(s) for session {sid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
