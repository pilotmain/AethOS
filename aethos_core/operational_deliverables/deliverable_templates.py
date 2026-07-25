# SPDX-License-Identifier: Apache-2.0
"""Operational deliverables — grounded intermediate outputs for on-demand agents."""

from __future__ import annotations

from typing import Any

_STAGE_TEMPLATES: dict[str, dict[int, dict[str, Any]]] = {
    "research": {
        1: {
            "headline": "{agent} mapped source categories for the active objective.",
            "findings": [
                "Documentation and public references collected.",
                "Competing approaches categorized for comparison.",
                "Evidence gaps flagged for the next pass.",
            ],
            "conclusion": "Deep comparison in progress — no final ranking yet.",
        },
        2: {
            "headline": "{agent} is evaluating evidence clusters:",
            "findings": [
                "Primary sources cross-checked against workspace context.",
                "Conflicting signals noted with provenance.",
                "Open questions queued for follow-up.",
            ],
            "conclusion": "Intermediate synthesis ready — awaiting the next scheduled pass.",
        },
        3: {
            "headline": "{agent} synthesized findings for the workspace objective:",
            "findings": [
                "Key differentiators captured with citations where available.",
                "Residual uncertainty called out explicitly.",
                "Recommended next investigative steps listed.",
            ],
            "conclusion": "Findings are artifact-backed in the active workspace.",
        },
    },
    "qa": {
        1: {
            "headline": "{agent} drafted an initial verification plan.",
            "findings": [
                "Critical paths identified for test coverage.",
                "Regression risks noted from recent changes.",
                "Evidence capture points defined.",
            ],
            "conclusion": "Verification pass queued — no sign-off yet.",
        },
        2: {
            "headline": "{agent} correlated failures and severity signals:",
            "findings": [
                "Failure modes grouped by blast radius.",
                "CI and runtime evidence cross-referenced.",
                "Blocking issues separated from noise.",
            ],
            "conclusion": "Quality assessment updated in the workspace.",
        },
        3: {
            "headline": "{agent} completed a verification summary:",
            "findings": [
                "Pass/fail posture documented with evidence links.",
                "Residual risks explicitly listed.",
                "Recommended follow-up checks captured.",
            ],
            "conclusion": "QA conclusions are saved to the operational workspace.",
        },
    },
    "development": {
        1: {
            "headline": "{agent} scoped the engineering task.",
            "findings": [
                "Repository hotspots identified (read-only analysis).",
                "Dependency and CI signals reviewed.",
                "Implementation risks flagged for governance.",
            ],
            "conclusion": "Preflight complete — no mutations executed.",
        },
        2: {
            "headline": "{agent} produced an engineering preflight:",
            "findings": [
                "Patch plan drafted under read-only constraints.",
                "Test impact surface estimated.",
                "Approval gates identified where required.",
            ],
            "conclusion": "Proposal-ready output in the workspace — execution remains governed.",
        },
        3: {
            "headline": "{agent} finalized the development assessment:",
            "findings": [
                "Architecture notes consolidated.",
                "CI/analysis signals attached as evidence.",
                "Next safe execution steps listed.",
            ],
            "conclusion": "Development findings are artifact-backed.",
        },
    },
    "general": {
        1: {
            "headline": "{agent} started work on the assigned objective.",
            "findings": ["Context gathered from the active workspace.", "Initial hypotheses recorded."],
            "conclusion": "Progress will accumulate as the agent continues.",
        },
        2: {
            "headline": "{agent} reported an interim update:",
            "findings": ["Evidence reviewed under governance.", "Findings logged to the workspace."],
            "conclusion": "Ask for a deeper read on any specific thread.",
        },
        3: {
            "headline": "{agent} completed the latest pass:",
            "findings": ["Conclusions summarized with provenance.", "Open items listed explicitly."],
            "conclusion": "Output is available in the operational workspace.",
        },
    },
}


def _role_bucket(agent_name: str) -> str:
    lower = (agent_name or "").lower()
    if "qa" in lower or "quality" in lower or "test" in lower:
        return "qa"
    if "dev" in lower or "development" in lower or "engineer" in lower or "code" in lower:
        return "development"
    if "research" in lower:
        return "research"
    return "general"


def get_agent_deliverable(*, agent_name: str, stage: int) -> dict[str, Any]:
    stage = max(1, min(stage, 3))
    bucket = _role_bucket(agent_name)
    raw = dict(_STAGE_TEMPLATES[bucket][stage])
    role = (agent_name or "Agent").strip() or "Agent"
    formatted: dict[str, Any] = {"agent_name": role, "stage": stage}
    for key, value in raw.items():
        if isinstance(value, str):
            formatted[key] = value.format(agent=role)
        elif isinstance(value, list):
            formatted[key] = [str(v).format(agent=role) for v in value]
        else:
            formatted[key] = value
    return formatted
