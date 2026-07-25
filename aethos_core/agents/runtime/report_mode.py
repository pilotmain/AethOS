# SPDX-License-Identifier: Apache-2.0
"""Report mode detection for intent-specific templates."""

from __future__ import annotations

import re

_DEPLOYMENT_FAIL_RX = re.compile(
    r"\banaly(?:z|s)e\s+why\b.*\b(?:railway|vercel|deployment)\b|"
    r"\b(?:railway|vercel)\b.*\b(?:deployment|deploy)\b.*\bfail",
    re.I,
)
_ARCH_RISK_RX = re.compile(r"\barchitecture\s+risks?\b|\banaly(?:z|s)e\s+architecture\s+risks?", re.I)
_PR_MODERN_RX = re.compile(r"\bpr\s+proposal\b.*\bdependenc|\bprepare\s+a\s+pr\s+proposal\b", re.I)


def infer_report_mode(goal: str) -> str:
    raw = (goal or "").strip()
    if _DEPLOYMENT_FAIL_RX.search(raw):
        return "deployment_failure"
    if _PR_MODERN_RX.search(raw):
        return "pr_proposal"
    if _ARCH_RISK_RX.search(raw):
        return "architecture_risk"
    return "generic"
