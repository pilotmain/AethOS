# SPDX-License-Identifier: Apache-2.0
"""Synthesis validation — output verification."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.synthesis_stubs import guard_output


def validate_synthesis_output(text: str) -> dict[str, Any]:
    return guard_output(text)
