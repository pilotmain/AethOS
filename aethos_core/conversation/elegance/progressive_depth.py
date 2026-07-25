# SPDX-License-Identifier: Apache-2.0
"""Progressive depth — layered detail."""

from __future__ import annotations


def trim_depth(text: str, *, max_lines: int = 40) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines]).strip()
