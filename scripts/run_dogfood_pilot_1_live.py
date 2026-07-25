#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Live dogfood-pilot-1 run — FIX 181 end-to-end harness toward PR Open."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SESSION = "dogfood-pilot-1"
REPO_ISSUE = "pilotmain/AethOS#1"
RECEIPT_DIR = ROOT / "data" / "dogfood_pilot_1_receipts"


def main() -> int:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        build_end_to_end_repo_development_pilot_harness,
        run_end_to_end_repo_development_pilot,
    )
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
        list_pilot_run_audits,
    )
    from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_service import (
        build_pilot_validation_trust_board,
    )
    from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
        build_repo_pilot_readiness_dashboard,
    )
    from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
    from aethos_core.software_delivery.issue_intake_scope_fidelity_service import (
        build_issue_intake_scope_fidelity_snapshot,
    )

    started_at = datetime.now(UTC).isoformat()
    readiness = build_repo_pilot_readiness_dashboard(session_id=SESSION)
    pilot_outcome = run_end_to_end_repo_development_pilot(session_id=SESSION, repo_issue=REPO_ISSUE)
    harness = build_end_to_end_repo_development_pilot_harness(session_id=SESSION)
    timeline = build_software_delivery_timeline(session_id=SESSION)
    fidelity = build_issue_intake_scope_fidelity_snapshot(session_id=SESSION)
    trust = build_pilot_validation_trust_board(session_id=SESSION)
    audits = list_pilot_run_audits(session_id=SESSION)

    receipt: dict[str, Any] = {
        "schema_version": "dogfood_pilot_1_live_receipt_v1",
        "session_id": SESSION,
        "repo_issue": REPO_ISSUE,
        "started_at": started_at,
        "completed_at": datetime.now(UTC).isoformat(),
        "fix_182_readiness_ok": readiness.ok,
        "fix_181_pilot_ok": pilot_outcome.ok,
        "fix_181_stages_completed": pilot_outcome.stages_completed,
        "fix_181_blockers": pilot_outcome.blockers,
        "fix_181_audit_id": pilot_outcome.audit_id,
        "fix_185_fidelity_ok": fidelity.get("ok"),
        "fix_185_fidelity_score": (fidelity.get("assessment") or {}).get("fidelity_score"),
        "fix_183_trust_ok": trust.ok,
        "fix_183_trust_recommendation": trust.pilot_validation_trust_board.get("trust_recommendation")
        if trust.ok
        else None,
        "fix_183_human_effort_score": trust.pilot_validation_trust_board.get("human_effort_score")
        if trust.ok
        else None,
        "pilot_audit_count": len(audits),
        "plan_goal": str(((timeline.get("plan") or {}).get("governed_plan") or {}).get("goal") or ""),
        "harness_pending_commands": harness.end_to_end_repo_development_pilot_harness.get("pending_command_count"),
    }

    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    receipt_path = RECEIPT_DIR / f"dogfood-pilot-1-{stamp}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    print("\n=== DOGFOOD PILOT 1 RECEIPT ===")
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in (
                    "fix_182_readiness_ok",
                    "fix_181_pilot_ok",
                    "fix_181_stages_completed",
                    "fix_181_audit_id",
                    "fix_185_fidelity_ok",
                    "fix_183_trust_ok",
                    "fix_183_trust_recommendation",
                )
            },
            indent=2,
        )
    )
    print(f"\nFull receipt: {receipt_path}")
    return 0 if pilot_outcome.audit_id else 1


if __name__ == "__main__":
    raise SystemExit(main())
