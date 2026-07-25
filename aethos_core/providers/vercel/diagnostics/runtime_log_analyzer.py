# SPDX-License-Identifier: Apache-2.0
"""Analyze Vercel runtime log excerpts."""

from __future__ import annotations

import re
from typing import Any

_RUNTIME_ERROR_RX = re.compile(
    r"\b(error|exception|unhandled|timeout|ECONNREFUSED|500|502|503|504|crash|fatal)\b",
    re.I,
)


def analyze_runtime_logs(log_payload: dict[str, Any]) -> dict[str, Any]:
    events = list(log_payload.get("events") or [])
    runtime_lines: list[str] = []
    for event in events:
        if not isinstance(event, dict):
            continue
        event_type = str(event.get("type") or "").lower()
        text = str(event.get("text") or "").strip()
        if not text:
            continue
        is_runtime = event_type in {"stdout", "stderr", "lambda", "function", "runtime", "fatal"}
        if is_runtime or _RUNTIME_ERROR_RX.search(text):
            if _RUNTIME_ERROR_RX.search(text) or event_type in {"stderr", "fatal", "lambda"}:
                runtime_lines.append(text[:400])
    if not runtime_lines:
        for line in log_payload.get("log_lines") or []:
            if _RUNTIME_ERROR_RX.search(str(line)):
                runtime_lines.append(str(line)[:400])
    runtime_lines = runtime_lines[:8]
    summary = "No runtime error lines detected in API log excerpt."
    if runtime_lines:
        summary = f"Detected {len(runtime_lines)} runtime error line(s) in deployment logs."
    return {
        "ok": bool(runtime_lines) or bool(log_payload.get("log_lines")),
        "runtime_lines": runtime_lines,
        "summary": summary,
        "deployment_id": log_payload.get("deployment_id"),
    }
