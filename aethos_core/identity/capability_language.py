# SPDX-License-Identifier: Apache-2.0
"""Capability language — human-centered operational explanations."""

from __future__ import annotations

from typing import Any


def describe_browser_observation(*, enabled: bool) -> str:
    if enabled:
        return (
            "Governed browser observation and evidence capture are available "
            "when operational investigation requires it."
        )
    return (
        "Governed browser observation is currently restricted. "
        "Operational guidance and public status checks remain available."
    )


def describe_execution_runtime(*, enabled: bool) -> str:
    if enabled:
        return (
            "Direct system execution is available through approval workflows "
            "and protected execution paths."
        )
    return (
        "Direct system execution is currently restricted. "
        "Governed operational actions remain available through approval workflows "
        "and protected execution paths."
    )


def describe_vercel_cli(*, available: bool) -> str:
    if available:
        return "Vercel CLI integration is available for governed read-only operational checks."
    return "Vercel CLI integration is not currently available on this runtime."


def describe_generative_intelligence(*, configured: bool) -> str:
    if configured:
        return "Generative intelligence is available for open-ended operational reasoning."
    return (
        "Generative intelligence is not currently configured. "
        "Governed operational responses remain fully available."
    )


def build_capability_overview(caps: dict[str, Any], *, generative_configured: bool) -> str:
    lines = [
        "**How I can help**",
        "",
        "I observe, correlate, explain, research, analyze, and prepare governed operational actions — "
        "while keeping you authoritative over execution.",
        "",
        "**Operational pathways**",
        f"- {describe_browser_observation(enabled=bool(caps.get('browser_automation_enabled')))}",
        f"- {describe_execution_runtime(enabled=bool(caps.get('host_executor_enabled')))}",
        f"- {describe_vercel_cli(available=bool(caps.get('vercel_cli_on_path')))}",
        f"- {describe_generative_intelligence(configured=generative_configured)}",
        "",
        "Tell me what you're working through — infrastructure, runtime integrity, deployment, or investigation.",
    ]
    return "\n".join(lines)


def runtime_status_lines(caps: dict[str, Any], *, connection: str, chat_ready: bool, provider_available: bool) -> list[str]:
    return [
        f"- Connection: **{connection}**",
        f"- Conversation ready: **{'yes' if chat_ready else 'no'}**",
        f"- Browser observation: **{'available' if caps.get('browser_automation_enabled') else 'restricted'}**",
        f"- System execution: **{'available' if caps.get('host_executor_enabled') else 'restricted'}**",
        f"- Vercel CLI: **{'available' if caps.get('vercel_cli_on_path') else 'unavailable'}**",
        f"- Generative intelligence: **{'available' if provider_available else 'offline'}**",
    ]
