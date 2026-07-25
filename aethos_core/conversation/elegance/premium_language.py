# SPDX-License-Identifier: Apache-2.0
"""Premium language — refined phrasing."""

from __future__ import annotations

import re


def refine_language(text: str) -> str:
    text = re.sub(r"\bI found that\b", "Here’s what stood out:", text, flags=re.I)
    text = re.sub(r"\bBased on my research\b", "Across the sources reviewed", text, flags=re.I)
    return text
