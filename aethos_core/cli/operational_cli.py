# SPDX-License-Identifier: Apache-2.0
"""Unified operational CLI — same runtime as chat."""

from __future__ import annotations

import argparse
import json
import sys

from aethos_core.cli.operator_cli import OPERATOR_DEFAULT_SESSION_ID


def cmd_operational(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aethos operational", add_help=False)
    parser.add_argument("--session-id", default=OPERATOR_DEFAULT_SESSION_ID)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("words", nargs="*")
    args, _unknown = parser.parse_known_args(argv or [])

    text = " ".join(args.words).strip()
    if not text:
        print("Usage: aethos operational show railway projects")
        print("       aethos operational show logs")
        print("       aethos operational continue")
        return 1

    from aethos_core.operational_session.operational_runtime import run_operational_turn

    result = run_operational_turn(text, session_id=args.session_id, channel="cli")
    if args.json:
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "intent": result.intent,
                    "reply": result.reply,
                    "meta": result.meta,
                    "used_llm": result.used_llm,
                },
                indent=2,
            )
        )
    else:
        print(result.reply)
    return 0 if result.ok else 1


def operational_help_lines() -> list[str]:
    return [
        "aethos operational show railway projects",
        "aethos operational show logs",
        "aethos operational deployment status",
        "aethos operational top 5 logs for killit",
        "aethos operational continue",
    ]
