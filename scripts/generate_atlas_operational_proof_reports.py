#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate WORKSTREAM_A2 Atlas Trader operational proof deliverables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DOCS = ROOT / "docs"


def _print_json(data: dict) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, default=str))


def main() -> int:
    parser = argparse.ArgumentParser(description="WORKSTREAM_A2 — Atlas Trader operational proof program")
    parser.add_argument("--session-id", default="default", help="Mission Control session id")
    parser.add_argument("--report", action="store_true", help="Write deliverable markdown reports to docs/")
    parser.add_argument("--json", action="store_true", help="Print composed program JSON to stdout")
    parser.add_argument("--run-pilot", type=int, choices=(1, 2, 3), help="Run FIX 193 pilot via existing path")
    parser.add_argument("--seed-expansion", action="store_true", help="Record FIX 187 expansion approval")
    args = parser.parse_args()

    if args.seed_expansion:
        from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
            PHASE_2_REPOSITORY_ORDER,
        )
        from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
            append_independent_repository_trust_expansion_record,
        )

        repository = PHASE_2_REPOSITORY_ORDER[1]
        record = append_independent_repository_trust_expansion_record(
            session_id=args.session_id,
            kind="repo_expansion_approval",
            content=f"Operator approves {repository} for WORKSTREAM_A2 operational proof",
            repository=repository,
        )
        print(f"Seeded FIX 187 expansion approval: {record.get('record_id', record)}")

    if args.run_pilot:
        from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_service import (
            run_atlas_trader_pilot_arc_pilot,
        )

        outcome = run_atlas_trader_pilot_arc_pilot(pilot_number=args.run_pilot)
        print(
            f"Pilot {args.run_pilot}: ok={outcome.ok} session={outcome.session_id} "
            f"audit={outcome.audit_id} blockers={outcome.blockers}"
        )
        if not outcome.ok:
            return 1

    from aethos_core.workstreams.atlas_operational_proof_program.atlas_operational_proof_program_renderer import (
        render_all_atlas_operational_proof_deliverables,
    )
    from aethos_core.workstreams.atlas_operational_proof_program.atlas_operational_proof_program_service import (
        build_atlas_operational_proof_program,
    )

    result = build_atlas_operational_proof_program(session_id=args.session_id)
    board = result.atlas_operational_proof_program

    if args.json or (not args.report and not args.run_pilot and not args.seed_expansion):
        _print_json(board)
        return 0 if result.ok else 1

    if args.report:
        DOCS.mkdir(parents=True, exist_ok=True)
        deliverables = render_all_atlas_operational_proof_deliverables(board)
        for filename, content in deliverables.items():
            path = DOCS / filename
            path.write_text(content + "\n", encoding="utf-8")
            print(f"Wrote {path}")
        return 0

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
