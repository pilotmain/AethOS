#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Generate WORKSTREAM_F1 first customer delivery pilot deliverables."""

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
    parser = argparse.ArgumentParser(description="WORKSTREAM_F1 — first customer delivery pilot")
    parser.add_argument("--session-id", default="default", help="Mission Control session id")
    parser.add_argument("--report", action="store_true", help="Write deliverable markdown reports to docs/")
    parser.add_argument("--json", action="store_true", help="Print composed program JSON to stdout")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run customer delivery pilot after intake (requires prior intake or uses default intake)",
    )
    args = parser.parse_args()

    if args.run:
        from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_executor import (
            intake_customer_delivery_request_from_text,
            run_customer_delivery_pilot,
        )
        from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
            get_latest_customer_delivery_request,
        )

        if get_latest_customer_delivery_request(session_id=args.session_id) is None:
            intake_customer_delivery_request_from_text(
                session_id=args.session_id,
                body=(
                    "goal=First customer delivery proof, "
                    "scope=small health-check endpoint, "
                    "type=health_check_endpoint, "
                    "success=verified governed delivery"
                ),
            )
        run_customer_delivery_pilot(session_id=args.session_id)

    from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_renderer import (
        render_all_first_customer_delivery_pilot_deliverables,
    )
    from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_service import (
        build_first_customer_delivery_pilot_program,
    )

    result = build_first_customer_delivery_pilot_program(session_id=args.session_id)
    board = result.first_customer_delivery_pilot_program

    if args.json or not args.report:
        _print_json(board)
        return 0 if result.ok else 1

    DOCS.mkdir(parents=True, exist_ok=True)
    deliverables = render_all_first_customer_delivery_pilot_deliverables(board)
    for filename, content in deliverables.items():
        path = DOCS / filename
        path.write_text(content + "\n", encoding="utf-8")
        print(f"Wrote {path}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
