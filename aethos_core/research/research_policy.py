# SPDX-License-Identifier: Apache-2.0
"""Research policy — blocked browser/search actions."""

from __future__ import annotations

import re

_BLOCKED_RX = re.compile(
    r"\b(login|log\s*in|sign\s*in|autofill|submit\s+form|fill\s+out|purchase|checkout|"
    r"captcha|paywall|scrape\s+all|bulk\s+scrape|post\s+to\s+twitter|post\s+to\s+linkedin)\b",
    re.I,
)


def evaluate_web_request(text: str) -> dict[str, str | bool]:
    raw = (text or "").strip()
    if _BLOCKED_RX.search(raw):
        return {"allowed": False, "reason": "Blocked interaction — login, forms, or bulk scraping are not permitted."}
    return {"allowed": True, "reason": ""}
