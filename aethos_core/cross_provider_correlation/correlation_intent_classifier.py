# SPDX-License-Identifier: Apache-2.0
"""Cross-provider correlation intent classification."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

CorrelationIntentKind = Literal["push_trace", "failure_boundary", "runtime_reached"]

_PUSH_TRACE_RX = re.compile(
    r"\b("
    r"what happened after\b.*\b(?:my\s+)?(?:latest\s+)?(?:github\s+)?push"
    r"|trace\b.*\b(?:latest\s+)?push\b.*\b(?:across|through)\b.*\bproviders?"
    r"|after my\b.*\bpush\b.*\b(?:deploy|vercel|railway|github)"
    r")\b",
    re.I,
)
_FAILURE_BOUNDARY_RX = re.compile(
    r"\b("
    r"did\b.*\bfail\b.*\bbecause of\b.*\b(?:github|vercel)"
    r"|(?:github|vercel)\b.*\bor\b.*\b(?:github|vercel)\b.*\bfail"
    r"|where is the failure boundary"
    r"|failure boundary"
    r"|did github or vercel fail"
    r")\b",
    re.I,
)
_RUNTIME_REACHED_RX = re.compile(
    r"\b("
    r"did\b.*\bdeployment\b.*\breach\b.*\bruntime"
    r"|did\b.*\bdeploy\b.*\bmake it\b.*\b(?:runtime|production|railway)"
    r"|reach runtime"
    r")\b",
    re.I,
)
_REPO_RX = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b")
_PROJECT_RX = re.compile(r"\b(?:project|app)\s+([A-Za-z0-9_.-]+)\b", re.I)


@dataclass(frozen=True)
class CorrelationIntent:
    kind: CorrelationIntentKind
    repository: str = ""
    project: str = ""


def is_cross_provider_correlation_request(text: str) -> bool:
    return classify_correlation_intent(text) is not None


def classify_correlation_intent(text: str) -> CorrelationIntent | None:
    raw = (text or "").strip()
    if not raw:
        return None
    if _FAILURE_BOUNDARY_RX.search(raw):
        kind: CorrelationIntentKind = "failure_boundary"
    elif _RUNTIME_REACHED_RX.search(raw):
        kind = "runtime_reached"
    elif _PUSH_TRACE_RX.search(raw):
        kind = "push_trace"
    else:
        return None
    repo_match = _REPO_RX.search(raw)
    project_match = _PROJECT_RX.search(raw)
    return CorrelationIntent(
        kind=kind,
        repository=repo_match.group(1).strip() if repo_match else "",
        project=project_match.group(1).strip() if project_match else "",
    )
