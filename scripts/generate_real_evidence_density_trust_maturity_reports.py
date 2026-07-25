#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate WORKSTREAM_G1 real evidence density & trust maturity deliverables."""

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
    parser = argparse.ArgumentParser(description="WORKSTREAM_G1 — real evidence density & trust maturity")
    parser.add_argument("--session-id", default="default", help="Mission Control program session id")
    parser.add_argument("--report", action="store_true", help="Write deliverable markdown reports to docs/")
    parser.add_argument("--json", action="store_true", help="Print composed program JSON to stdout")
    args = parser.parse_args()

    from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_renderer import (
        render_all_evidence_maturity_deliverables,
    )
    from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_service import (
        build_real_evidence_density_trust_maturity_program,
    )

    result = build_real_evidence_density_trust_maturity_program(session_id=args.session_id)
    board = result.real_evidence_density_trust_maturity_program

    if args.json or not args.report:
        _print_json(board)
        return 0 if result.ok else 1

    DOCS.mkdir(parents=True, exist_ok=True)
    deliverables = render_all_evidence_maturity_deliverables(board)
    for filename, content in deliverables.items():
        path = DOCS / filename
        path.write_text(content + "\n", encoding="utf-8")
        print(f"Wrote {path}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
