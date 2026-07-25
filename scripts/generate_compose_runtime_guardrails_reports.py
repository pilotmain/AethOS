#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate WORKSTREAM_E4 compose runtime guardrails deliverables."""

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
    parser = argparse.ArgumentParser(description="WORKSTREAM_E4 — compose runtime guardrails")
    parser.add_argument("--session-id", default="default", help="Mission Control session id")
    parser.add_argument("--report", action="store_true", help="Write deliverable markdown reports to docs/")
    parser.add_argument("--json", action="store_true", help="Print composed program JSON to stdout")
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Enforce runtime guardrails before composing reports",
    )
    parser.add_argument(
        "--benchmark",
        choices=(
            "run compose benchmark",
            "run full evidence benchmark",
            "run critical compose benchmark",
        ),
        help="Run an explicit benchmark command (requires intentional heavy compose mode)",
    )
    args = parser.parse_args()

    if args.enforce:
        from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_executor import (
            enforce_runtime_guardrails,
        )

        enforce_runtime_guardrails(session_id=args.session_id)

    if args.benchmark:
        from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_executor import (
            run_benchmark_command,
        )

        run_benchmark_command(session_id=args.session_id, command_text=args.benchmark)

    from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_renderer import (
        render_all_compose_runtime_guardrails_deliverables,
    )
    from aethos_core.workstreams.compose_runtime_guardrails_program.compose_runtime_guardrails_program_service import (
        build_compose_runtime_guardrails_program,
    )

    result = build_compose_runtime_guardrails_program(session_id=args.session_id)
    board = result.compose_runtime_guardrails_program

    if args.json or not args.report:
        _print_json(board)
        return 0 if result.ok else 1

    DOCS.mkdir(parents=True, exist_ok=True)
    deliverables = render_all_compose_runtime_guardrails_deliverables(board)
    for filename, content in deliverables.items():
        path = DOCS / filename
        path.write_text(content + "\n", encoding="utf-8")
        print(f"Wrote {path}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
