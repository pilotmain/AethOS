# SPDX-License-Identifier: Apache-2.0
"""Geographic normalization — location consistency."""

from __future__ import annotations

import re


def normalize_geography(text: str, *, filter_region: str | None = None) -> str:
    m = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*([A-Z]{2})\b", text)
    if m:
        loc = f"{m.group(1)}, {m.group(2)}"
        if filter_region and filter_region.lower() not in loc.lower() and filter_region.lower() not in text.lower():
            return ""
        return loc
    if filter_region and filter_region.lower() in text.lower():
        return filter_region
    return ""
