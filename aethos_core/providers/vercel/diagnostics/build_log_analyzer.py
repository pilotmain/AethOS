# SPDX-License-Identifier: Apache-2.0
"""Analyze Vercel build log excerpts for operator findings."""

from __future__ import annotations

import re
from typing import Any

_BUILD_ERROR_RX = re.compile(
    r"\b(error|failed|failure|exception|npm ERR!|ERR!|ELIFECYCLE|command failed|build failed)\b",
    re.I,
)


def analyze_build_logs(log_payload: dict[str, Any]) -> dict[str, Any]:
    lines = list(log_payload.get("log_lines") or [])
    events = list(log_payload.get("events") or [])
    error_lines: list[str] = []
    for line in lines:
        if _BUILD_ERROR_RX.search(line):
            error_lines.append(line[:400])
    if not error_lines:
        for event in events:
            if not isinstance(event, dict):
                continue
            text = str(event.get("text") or "")
            event_type = str(event.get("type") or "").lower()
            if event_type in {"stderr", "error", "command", "build"} and text and _BUILD_ERROR_RX.search(text):
                error_lines.append(text[:400])
    error_lines = error_lines[:8]
    summary = "No build error lines detected in API log excerpt."
    if error_lines:
        summary = f"Detected {len(error_lines)} build error line(s) in deployment logs."
    return {
        "ok": bool(log_payload.get("ok")) or bool(lines),
        "error_lines": error_lines,
        "line_count": len(lines),
        "summary": summary,
        "deployment_id": log_payload.get("deployment_id"),
    }
