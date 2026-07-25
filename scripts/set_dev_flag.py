#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Set a known .env flag for local manual testing — does not restart the API."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
EXAMPLE_PATH = ROOT / ".env.example"

ALLOWED: dict[str, tuple[str, ...]] = {
    "BROWSER_AUTOMATION_ENABLED": ("true", "false"),
    "HOST_EXECUTOR_ENABLED": ("true", "false"),
    "USE_REAL_LLM": ("true", "false"),
}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Update a single allowed flag in .env (local dev only). Restart API after use.",
    )
    p.add_argument("flag", choices=sorted(ALLOWED.keys()), help="Canonical env variable name")
    p.add_argument("value", choices=("true", "false"), help="true or false")
    p.add_argument(
        "--create",
        action="store_true",
        help="Create .env from .env.example if missing",
    )
    return p.parse_args()


def _ensure_env(create: bool) -> None:
    if ENV_PATH.exists():
        return
    if not create:
        print(
            f"No .env at {ENV_PATH}. Copy .env.example or pass --create.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not EXAMPLE_PATH.exists():
        print(f"Missing {EXAMPLE_PATH}", file=sys.stderr)
        sys.exit(1)
    ENV_PATH.write_text(EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Created {ENV_PATH} from .env.example")


def _set_flag(text: str, flag: str, value: str) -> tuple[str, bool]:
    pattern = re.compile(rf"^({re.escape(flag)})=.*$", re.MULTILINE)
    replacement = f"{flag}={value}"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1), True
    suffix = "\n" if text and not text.endswith("\n") else ""
    return f"{text}{suffix}{replacement}\n", False


def main() -> None:
    args = _parse_args()
    flag = args.flag
    value = args.value.lower()
    if value not in ALLOWED[flag]:
        print(f"Invalid value for {flag}: {value}", file=sys.stderr)
        sys.exit(1)

    _ensure_env(args.create)
    original = ENV_PATH.read_text(encoding="utf-8")
    updated, replaced = _set_flag(original, flag, value)
    ENV_PATH.write_text(updated, encoding="utf-8")

    action = "Updated" if replaced else "Appended"
    print(f"{action} {flag}={value} in {ENV_PATH}")
    print("Restart the API for the change to take effect:")
    print("  .venv/bin/uvicorn aethos_core.api.main:app --reload --port 8010")
    if flag == "BROWSER_AUTOMATION_ENABLED" and value == "true":
        print()
        print("Note: BROWSER_AUTOMATION_ENABLED=true enables the Phase 7 foundation only.")
        print("It does NOT open a real browser until Phase 8+.")


if __name__ == "__main__":
    main()
