# SPDX-License-Identifier: Apache-2.0
"""Browser evidence intent detection — channel-agnostic."""

from __future__ import annotations

import re
from typing import Any

_BLOCKED_RX = re.compile(
    r"\b(click|submit|autofill|purchase|automatically)\b.*\b(button|form|deploy|checkout)\b|"
    r"\bclick\b.*\bautomatically\b",
    re.I,
)

_CAPTURE_RX = re.compile(
    r"\b(capture|take|show)\b.*\b(screenshot|screen\s+shot|browser\s+evidence|deployment\s+evidence)\b|"
    r"\b(capture\s+screenshot|browser\s+evidence|deployment\s+evidence)\b",
    re.I,
)

_METADATA_RX = re.compile(
    r"\b(inspect|show|capture)\b.*\b(page\s+metadata|metadata)\b|"
    r"\bmetadata\b.*\b(for|of|on)\b",
    re.I,
)

_EVIDENCE_LIST_RX = re.compile(
    r"\b(show|list)\b.*\bbrowser\s+evidence\b",
    re.I,
)


def is_browser_evidence_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _EVIDENCE_LIST_RX.search(raw):
        return True
    if _BLOCKED_RX.search(raw):
        return True
    return bool(_CAPTURE_RX.search(raw) or _METADATA_RX.search(raw))


def infer_browser_evidence_job(text: str) -> tuple[str, dict[str, Any]] | None:
    raw = (text or "").strip()
    if not is_browser_evidence_request(raw):
        return None

    from aethos_core.browser.runtime.browser_policy import classify_user_request
    from aethos_core.browser.runtime.browser_runtime import extract_url_from_request

    if _EVIDENCE_LIST_RX.search(raw):
        return (
            "browser_evidence_list",
            {"user_request": raw, "operation_type": "browser_evidence_list"},
        )

    policy = classify_user_request(raw)
    capture_type = str(policy.get("capture_type") or "screenshot")
    if _METADATA_RX.search(raw):
        capture_type = "metadata"
    deployment_evidence = bool(
        re.search(r"\bdeployment\s+evidence\b", raw, re.I)
        or (re.search(r"\bbrowser\s+evidence\b", raw, re.I) and not re.search(r"https?://", raw, re.I))
    )
    url = ""
    if not deployment_evidence:
        url = extract_url_from_request(raw)

    return (
        "browser_capture_execution",
        {
            "user_request": raw,
            "operation_type": "browser_capture",
            "capture_type": "full" if deployment_evidence else capture_type,
            "target_url": url,
            "deployment_evidence": deployment_evidence,
            "blocked_request": not policy.get("allowed", True),
            "policy": policy,
        },
    )
