# SPDX-License-Identifier: Apache-2.0
"""Intent-specific multi-agent report templates."""

from __future__ import annotations

from typing import Any

from aethos_core.agents.runtime.agent_result_contract import format_agent_contract_block


def render_deployment_failure_report(merged: dict[str, Any]) -> str:
    conf = merged.get("confidence") or {}
    sev = merged.get("severity_authority") or {}
    conclusions = merged.get("conclusions") or {}
    lines = [
        "# Deployment failure analysis (evidence-grounded)",
        "",
        f"**Goal:** {merged.get('goal')}",
        f"**Status:** {merged.get('status')}",
        f"**Severity:** {sev.get('severity', merged.get('severity', 'LOW'))}",
        f"**Severity reason:** {'; '.join(sev.get('severity_reason') or []) or '—'}",
        f"**Confidence:** {conf.get('level', 'low')} — {', '.join(conf.get('reasons') or []) or 'limited evidence'}",
        "",
    ]
    intel = merged.get("deployment_intelligence") or {}
    latest = intel.get("latest_deployment") or {}
    if latest.get("id"):
        lines.extend(
            [
                "## Deployment timeline",
                f"- Latest: `{latest.get('id')}` · **{latest.get('state')}** · {latest.get('started_label', '—')}",
                "",
            ]
        )
    corr = merged.get("correlation") or {}
    if corr.get("temporal") or corr.get("structural") or corr.get("operational"):
        lines.extend(["## Correlations"])
        for group in ("temporal", "structural", "operational"):
            for row in corr.get(group) or []:
                lines.append(f"- [{group}] {row.get('detail')}")
        lines.append("")
    if conf.get("gaps"):
        lines.extend(["## Confidence reasoning", f"**Level:** {conf.get('level', 'low')}"])
        for g in conf.get("gaps") or []:
            lines.append(f"- Gap: {g}")
        lines.append("")
    if merged.get("recurring_patterns"):
        lines.extend(["## Recurring patterns"])
        for p in merged["recurring_patterns"][:5]:
            lines.append(f"- {p}")
        lines.append("")
    lines.extend(
        [
            "## What we checked",
        ]
    )
    for step in merged.get("timeline") or []:
        lines.append(f"- **{step.get('agent_id')}** — {step.get('task')} ({step.get('status')})")
    lines.extend(["", "## Confirmed findings"])
    for f in conclusions.get("confirmed") or []:
        lines.append(f"- {f}")
    if not conclusions.get("confirmed"):
        lines.append("- No confirmed deployment failure from provider evidence.")
    lines.extend(["", "## Likely hypothesis"])
    for h in conclusions.get("hypotheses") or []:
        lines.append(f"- {h}")
    if not conclusions.get("hypotheses"):
        lines.append("- None — evidence insufficient for a supported hypothesis.")
    lines.extend(["", "## Related signals"])
    for s in conclusions.get("signals") or []:
        lines.append(f"- {s}")
    if not conclusions.get("signals"):
        lines.append("- None recorded.")
    lines.extend(["", "## Evidence gaps"])
    for g in conclusions.get("gaps") or []:
        lines.append(f"- {g}")
    if merged.get("evidence_summaries"):
        lines.extend(["", "## Evidence attribution"])
        for e in merged["evidence_summaries"][:12]:
            lines.append(f"- {e.get('display') or e.get('summary')}")
    if merged.get("next_steps"):
        lines.extend(["", "## Recommended next steps"])
        for n in merged["next_steps"][:5]:
            lines.append(f"- {n}")
    if merged.get("agent_contracts"):
        lines.extend(["", "## Agent detail"])
        for c in merged["agent_contracts"]:
            lines.append(format_agent_contract_block(c))
            lines.append("")
    lines.extend(["", _governance_footer()])
    return "\n".join(lines)


def render_pr_proposal_report(merged: dict[str, Any]) -> str:
    proposal = merged.get("pr_proposal") or {}
    targets = proposal.get("modernization_targets") or []
    sev = merged.get("severity_authority") or {}
    lines = [
        f"# PR Proposal: {proposal.get('title') or 'Dependency modernization'}",
        "",
        f"**Objective:** {proposal.get('objective') or 'Reduce dependency risk through governed modernization.'}",
        f"**Why now:** {proposal.get('why_now') or 'Dependency audit flagged actionable upgrade targets.'}",
        f"**Risk level:** {sev.get('severity', 'MEDIUM')}",
        "",
        "## Dependency targets",
    ]
    if targets:
        for t in targets[:12]:
            if isinstance(t, dict):
                lines.append(f"- `{t.get('package')}` ({t.get('ecosystem')}) — {t.get('reason')}")
            else:
                lines.append(f"- {t}")
    else:
        lines.append("- Run dependency audit to populate targets.")
    lines.extend(["", "## Proposed phases"])
    for i, phase in enumerate(proposal.get("phased_migration") or [], 1):
        lines.append(f"{i}. {phase}")
    lines.extend(["", "## Required validation"])
    for step in proposal.get("required_validation") or proposal.get("verification_plan") or []:
        lines.append(f"- {step}")
    if proposal.get("dependency_table"):
        lines.extend(["", "## Dependency matrix"])
        for row in proposal["dependency_table"][:8]:
            lines.append(f"- `{row.get('package')}`: {row.get('current')} → {row.get('target')} ({row.get('risk')} risk)")
    lines.extend(["", "## Rollback plan", proposal.get("rollback_plan") or "Revert branch / discard patch — no auto-merge."])
    lines.extend(
        [
            "",
            "## Write status",
            "**Readonly proposal only.** No branch, commit, push, or merge performed.",
            "Approval required before any governed write.",
        ]
    )
    if merged.get("evidence_summaries"):
        lines.extend(["", "## Supporting evidence"])
        for e in merged["evidence_summaries"][:8]:
            lines.append(f"- {e.get('display') or e.get('summary')}")
    if merged.get("agent_contracts"):
        lines.extend(["", "## Agent detail"])
        for c in merged["agent_contracts"]:
            lines.append(format_agent_contract_block(c))
            lines.append("")
    lines.extend(["", _governance_footer()])
    return "\n".join(lines)


def render_architecture_risk_report(merged: dict[str, Any]) -> str:
    arch = merged.get("architecture_analysis") or {}
    sev = merged.get("severity_authority") or {}
    health = arch.get("architecture_health") or {}
    lines = [
        "# Architecture risk analysis (operational intelligence)",
        "",
        f"**Goal:** {merged.get('goal')}",
        f"**Architecture health:** {health.get('architecture_health', '—')}/100",
        f"**Risk level:** {health.get('risk_level', sev.get('severity', 'LOW'))}",
        f"**Severity:** {sev.get('severity', 'LOW')}",
        f"**Severity reason:** {'; '.join(sev.get('severity_reason') or []) or '—'}",
        "",
        "## Top risks",
    ]
    for t in arch.get("top_risks") or []:
        lines.append(f"- {t}")
    lines.extend(["", "## Risk areas"])
    for b in arch.get("bottlenecks") or []:
        lines.append(f"- **{b.get('area')}** — {b.get('detail')}")
    if not arch.get("bottlenecks"):
        lines.append("- No critical bottlenecks flagged in architecture scan.")
    lines.extend(["", "## Evidence"])
    for layer in (arch.get("layers") or [])[:8]:
        lines.append(f"- {layer.get('layer')} — {layer.get('role')}")
    lines.extend(["", "## Governance observations"])
    for g in arch.get("governance_observations") or []:
        lines.append(f"- {g}")
    lines.extend(["", "## Recommendations"])
    for r in merged.get("recommendations") or arch.get("scalability_observations") or []:
        lines.append(f"- {r}")
    if merged.get("evidence_summaries"):
        lines.extend(["", "## Evidence attribution"])
        for e in merged["evidence_summaries"][:8]:
            lines.append(f"- {e.get('display') or e.get('summary')}")
    if merged.get("agent_contracts"):
        lines.extend(["", "## Agent detail"])
        for c in merged["agent_contracts"]:
            lines.append(format_agent_contract_block(c))
            lines.append("")
    lines.extend(["", _governance_footer()])
    return "\n".join(lines)


def render_merged_report(merged: dict[str, Any]) -> str:
    mode = str(merged.get("report_mode") or "generic")
    if mode == "deployment_failure":
        return render_deployment_failure_report(merged)
    if mode == "pr_proposal":
        return render_pr_proposal_report(merged)
    if mode == "architecture_risk":
        return render_architecture_risk_report(merged)
    return _render_generic_report(merged)


def _render_generic_report(merged: dict[str, Any]) -> str:
    conf = merged.get("confidence") or {}
    sev = merged.get("severity_authority") or {}
    lines = [
        "# Multi-agent operational intelligence report (governed)",
        "",
        f"**Goal:** {merged.get('goal')}",
        f"**Status:** {merged.get('status')}",
        f"**Severity:** {sev.get('severity', merged.get('severity', 'LOW'))}",
        f"**Confidence:** {conf.get('level', 'low')}",
    ]
    if merged.get("evidence_summaries"):
        lines.extend(["", "## Evidence"])
        for e in merged["evidence_summaries"][:10]:
            lines.append(f"- {e.get('display') or e.get('summary')}")
    if merged.get("agent_contracts"):
        lines.extend(["", "## Agents"])
        for c in merged["agent_contracts"]:
            lines.append(format_agent_contract_block(c))
            lines.append("")
    lines.extend(["", _governance_footer()])
    return "\n".join(lines)


def _governance_footer() -> str:
    return (
        "**Governance:** agents are workers — orchestration retains authority.\n"
        "**Blocked:** direct mutations · auto-merge · self-spawn · unrestricted shell"
    )
