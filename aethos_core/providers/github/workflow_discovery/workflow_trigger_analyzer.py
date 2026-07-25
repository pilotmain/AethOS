# SPDX-License-Identifier: Apache-2.0
"""Analyze GitHub workflow YAML triggers."""

from __future__ import annotations

import re
from typing import Any

_KNOWN_TRIGGERS = frozenset(
    {
        "push",
        "pull_request",
        "pull_request_target",
        "workflow_dispatch",
        "schedule",
        "release",
        "workflow_call",
        "repository_dispatch",
        "workflow_run",
        "issues",
        "issue_comment",
    }
)


def analyze_workflow_triggers(content: str, *, filename: str = "") -> dict[str, Any]:
    text = content or ""
    triggers = _extract_on_triggers(text)
    parse_ok = bool(text.strip()) and (bool(triggers) or "on:" in text)
    parse_error = None
    if text.strip() and not triggers and "on:" not in text:
        parse_ok = False
        parse_error = "Could not locate an `on:` trigger block."
    return {
        "filename": filename,
        "parse_ok": parse_ok,
        "parse_error": parse_error,
        "triggers": triggers,
        "has_workflow_dispatch": "workflow_dispatch" in triggers,
        "has_push": "push" in triggers,
        "has_pull_request": any(t in triggers for t in ("pull_request", "pull_request_target")),
        "has_schedule": "schedule" in triggers,
    }


def analyze_workflow_files(workflow_files: list[dict[str, Any]]) -> dict[str, Any]:
    analyzed: list[dict[str, Any]] = []
    any_dispatch = False
    any_push = False
    any_pr = False
    parse_failures: list[str] = []
    for row in workflow_files:
        if not isinstance(row, dict):
            continue
        content = str(row.get("content") or "")
        name = str(row.get("name") or "")
        result = analyze_workflow_triggers(content, filename=name)
        if not result.get("parse_ok") and content.strip():
            parse_failures.append(name or "unknown")
        any_dispatch = any_dispatch or bool(result.get("has_workflow_dispatch"))
        any_push = any_push or bool(result.get("has_push"))
        any_pr = any_pr or bool(result.get("has_pull_request"))
        analyzed.append(result)
    all_triggers = sorted({trigger for row in analyzed for trigger in row.get("triggers") or []})
    return {
        "workflows": analyzed,
        "workflow_count": len(analyzed),
        "all_triggers": all_triggers,
        "has_workflow_dispatch": any_dispatch,
        "has_push_trigger": any_push,
        "has_pull_request_trigger": any_pr,
        "parse_failures": parse_failures,
    }


def _extract_on_triggers(text: str) -> list[str]:
    triggers: list[str] = []
    lines = text.splitlines()
    in_on = False
    on_indent = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.match(r"^on\s*:", stripped):
            in_on = True
            on_indent = len(line) - len(line.lstrip())
            inline = stripped.split(":", 1)[1].strip()
            if inline and inline not in {">", "|"}:
                triggers.extend(_split_trigger_tokens(inline))
            continue
        if not in_on:
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= on_indent and ":" in stripped:
            break
        if ":" in stripped:
            key = stripped.split(":", 1)[0].strip().strip("-")
            if key in _KNOWN_TRIGGERS:
                triggers.append(key)
            elif key and not key.startswith("[") and indent == on_indent + 2:
                triggers.append(key)
    return _dedupe(triggers)


def _split_trigger_tokens(raw: str) -> list[str]:
    cleaned = raw.strip().strip("[]")
    if not cleaned:
        return []
    if cleaned.startswith("["):
        parts = [part.strip().strip("'\"") for part in cleaned.strip("[]").split(",")]
        return [part for part in parts if part]
    token = cleaned.split()[0].strip("'\"")
    return [token] if token else []


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
