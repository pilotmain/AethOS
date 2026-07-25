# SPDX-License-Identifier: Apache-2.0
"""Response normalizer — clean human output."""

from __future__ import annotations

import re
from typing import Any


def normalize_response(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    text = re.sub(r"^#+\s+Research synthesis\s*$", "", text, flags=re.I | re.M)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text.strip()


def normalize_count_label(text: str, *, expected: int | None) -> str:
    if expected is None:
        return text
    text = re.sub(r"\btop\s+ten\b", f"top {expected}", text, flags=re.I)
    text = re.sub(r"\btop\s+\d+\b", f"top {expected}", text, flags=re.I)
    return text
