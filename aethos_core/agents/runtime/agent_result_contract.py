# SPDX-License-Identifier: Apache-2.0
"""Standard agent result contract — structured operational output."""

from __future__ import annotations

from typing import Any


def build_agent_contract(
    *,
    agent_id: str,
    task: str,
    status: str,
    findings: list[str],
    evidence: list[str],
    limitations: list[str],
    next_steps: list[str],
    confidence: str = "low",
    substrate_invoked: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "task": task,
        "status": status,
        "findings": findings,
        "evidence": evidence,
        "limitations": limitations,
        "next_steps": next_steps,
        "confidence": confidence,
        "substrate_invoked": substrate_invoked or [],
    }


def format_agent_contract_block(contract: dict[str, Any]) -> str:
    label = str(contract.get("agent_id") or "agent").replace("_", " ").title()
    lines = [
        f"### {label}",
        f"- **Task:** {contract.get('task') or '—'}",
        f"- **Status:** {contract.get('status') or '—'}",
        f"- **Confidence:** {contract.get('confidence') or 'low'}",
    ]
    if contract.get("evidence"):
        lines.append("- **Evidence:**")
        for e in contract["evidence"][:6]:
            lines.append(f"  - {e}")
    if contract.get("findings"):
        lines.append("- **Findings:**")
        for f in contract["findings"][:6]:
            lines.append(f"  - {f}")
    if contract.get("limitations"):
        lines.append("- **Limitations:**")
        for lim in contract["limitations"][:4]:
            lines.append(f"  - {lim}")
    if contract.get("next_steps"):
        lines.append("- **Next step:**")
        for n in contract["next_steps"][:3]:
            lines.append(f"  - {n}")
    return "\n".join(lines)


def attach_contract(row: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    row = dict(row)
    row["contract"] = contract
    return row
