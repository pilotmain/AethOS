#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate WORKSTREAM_E3 intelligence scalability implementation deliverables."""

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
    parser = argparse.ArgumentParser(description="WORKSTREAM_E3 — intelligence scalability implementation")
    parser.add_argument("--session-id", default="default", help="Mission Control session id")
    parser.add_argument("--report", action="store_true", help="Write deliverable markdown reports to docs/")
    parser.add_argument("--json", action="store_true", help="Print composed program JSON to stdout")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run scalability implementation before composing reports",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full FIX 322/323 compose during --execute (slow; default is lightweight)",
    )
    args = parser.parse_args()

    if args.execute:
        from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_executor import (
            execute_scalability_implementation,
        )

        execute_scalability_implementation(session_id=args.session_id, lightweight=not args.full)

    from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_renderer import (
        render_all_intelligence_scalability_implementation_deliverables,
    )
    from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalability_implementation_program_service import (
        build_intelligence_scalability_implementation_program,
    )

    result = build_intelligence_scalability_implementation_program(session_id=args.session_id)
    board = result.intelligence_scalability_implementation_program

    if args.json or not args.report:
        _print_json(board)
        return 0 if result.ok else 1

    DOCS.mkdir(parents=True, exist_ok=True)
    deliverables = render_all_intelligence_scalability_implementation_deliverables(board)
    for filename, content in deliverables.items():
        path = DOCS / filename
        path.write_text(content + "\n", encoding="utf-8")
        print(f"Wrote {path}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
