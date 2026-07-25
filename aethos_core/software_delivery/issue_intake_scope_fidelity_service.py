# SPDX-License-Identifier: Apache-2.0
"""FIX 185 — issue intake scope fidelity (preserve GitHub issue scope)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aethos_core.software_delivery.issue_intake_scope_fidelity_contract import (
    FIDELITY_ESCALATION_THRESHOLD,
    FORBIDDEN_OUT_OF_SCOPE_PREFIXES,
    WORKFLOW_REFRAME_GOAL_RX,
)

_PATH_RX = re.compile(
    r"`([^`\n]+\.[A-Za-z0-9]+)`|(?:^|\s)((?:[\w.-]+/)+[\w.-]+\.[A-Za-z0-9]+)",
    re.MULTILINE,
)
_SCOPE_SECTION_RX = re.compile(
    r"(?is)(?:^|\n)#+\s*scope(?:\s*\(?bounded\)?)?[^\n]*\n(.+?)(?:\n#+\s|\Z)",
)
_OUT_OF_SCOPE_SECTION_RX = re.compile(
    r"(?is)(?:^|\n)#+\s*out\s+of\s+scope[^\n]*\n(.+?)(?:\n#+\s|\Z)",
)
_SECTION_TITLE_RX = re.compile(r"(?i)section\s+title:\s*(.+?)(?:\n|$)")
_DOGFOOD_RX = re.compile(r"\b(dogfood|pilot execution log|pilot validation)\b", re.I)
_WORKFLOW_HEURISTIC_RX = re.compile(
    r"\bfix\b.*\b(?:github\s+)?workflow\b|\bworkflow\s+rerun\b",
    re.I,
)


@dataclass(frozen=True)
class IssueScopeFidelityEnvelope:
    intended_goal: str
    expected_files: list[str]
    out_of_scope_constraints: list[str]
    explicit_bounded_scope: bool
    scope_confidence: str
    issue_title: str
    issue_body_excerpt: str
    forbidden_file_prefixes: list[str]
    source: str = "github_issue"


@dataclass(frozen=True)
class PlanScopeFidelityAssessment:
    ok: bool
    fidelity_score: int
    escalation_required: bool
    escalation_reasons: list[str]
    plan_goal_divergence: bool
    plan_goal_divergence_detail: str
    forbidden_files_in_plan: list[str]
    detail: str = ""


def _normalize_path(path: str) -> str:
    return (path or "").strip().replace("\\", "/").lstrip("./")


def _extract_paths_from_text(text: str) -> list[str]:
    found: list[str] = []
    for match in _PATH_RX.finditer(text or ""):
        candidate = _normalize_path(match.group(1) or match.group(2) or "")
        if candidate and candidate not in found:
            found.append(candidate)
    return found


def _extract_list_items(section: str) -> list[str]:
    items: list[str] = []
    for line in (section or "").splitlines():
        stripped = line.strip()
        if stripped.startswith(("-", "*")):
            items.append(stripped.lstrip("-* ").strip())
    return items


def extract_issue_scope_fidelity(*, issue: dict[str, Any], repo: Path | None = None) -> IssueScopeFidelityEnvelope:
    title = str(issue.get("title") or "").strip()
    body = str(issue.get("body") or "").strip()
    full_text = f"{title}\n{body}"

    scope_section = ""
    scope_match = _SCOPE_SECTION_RX.search(body)
    if scope_match:
        scope_section = scope_match.group(1).strip()

    out_section = ""
    out_match = _OUT_OF_SCOPE_SECTION_RX.search(body)
    if out_match:
        out_section = out_match.group(1).strip()

    expected = _extract_paths_from_text(scope_section) if scope_section else _extract_paths_from_text(body)
    if repo:
        expected = [p for p in expected if (repo / p).is_file()]

    out_of_scope = _extract_list_items(out_section)
    if not out_of_scope and out_section:
        out_of_scope = [line.strip() for line in out_section.splitlines() if line.strip()][:12]

    section_title_match = _SECTION_TITLE_RX.search(full_text)
    if section_title_match:
        intended_goal = f"{title} — {section_title_match.group(1).strip()}"
    elif _DOGFOOD_RX.search(full_text):
        intended_goal = title or "Bounded dogfood issue scope"
    else:
        intended_goal = title or "Issue-authored scope"

    explicit_bounded_scope = bool(scope_section and expected)
    scope_confidence = "high" if explicit_bounded_scope else "medium" if expected else "low"

    forbidden_prefixes = [prefix for prefix, _ in FORBIDDEN_OUT_OF_SCOPE_PREFIXES]
    for item in out_of_scope:
        lower = item.lower()
        if "workflow" in lower:
            forbidden_prefixes.append(".github/workflows/")
        if "provider" in lower:
            forbidden_prefixes.append("aethos_core/providers/")
        if "mutation" in lower:
            forbidden_prefixes.append("aethos_core/operations/mutations/")

    return IssueScopeFidelityEnvelope(
        intended_goal=intended_goal,
        expected_files=expected,
        out_of_scope_constraints=out_of_scope,
        explicit_bounded_scope=explicit_bounded_scope,
        scope_confidence=scope_confidence,
        issue_title=title,
        issue_body_excerpt=body[:500],
        forbidden_file_prefixes=sorted(set(forbidden_prefixes)),
        source="github_issue",
    )


def build_fidelity_governed_task(
    *,
    issue: dict[str, Any],
    envelope: IssueScopeFidelityEnvelope,
    repo: Path | None = None,
) -> dict[str, Any]:
    """Task derived from issue scope fidelity — not workflow heuristics."""
    body = f"{issue.get('title') or ''}\n{issue.get('body') or ''}"
    files = list(envelope.expected_files)
    if repo and not files:
        files = _extract_paths_from_text(body)
        files = [p for p in files if (repo / p).is_file()]
    return {
        "task_id": f"etask-fidelity-{issue.get('number') or 'issue'}",
        "kind": "bounded_issue_scope",
        "title": envelope.intended_goal,
        "problem_summary": envelope.issue_body_excerpt[:240] or envelope.intended_goal,
        "likely_cause": "Bounded issue scope — root cause analysis deferred to planning review.",
        "affected_files": files,
        "test_scope": ["tests/"],
        "risk_tier": "E1_proposal_only",
        "proposed_fix": envelope.intended_goal,
        "labels": ["engineering", "bounded_scope"],
        "source": "issue_intake_scope_fidelity",
        "raw_request": body[:500],
        "issue_number": issue.get("number"),
        "issue_url": issue.get("html_url"),
    }


def should_use_scope_fidelity_task(*, issue: dict[str, Any], envelope: IssueScopeFidelityEnvelope) -> bool:
    if envelope.explicit_bounded_scope and envelope.expected_files:
        return True
    title_body = f"{issue.get('title') or ''}\n{issue.get('body') or ''}"
    if _DOGFOOD_RX.search(title_body) and envelope.expected_files:
        return True
    if envelope.expected_files and not _WORKFLOW_HEURISTIC_RX.search(title_body):
        return True
    return False


def envelope_to_plan_payload(envelope: IssueScopeFidelityEnvelope) -> dict[str, Any]:
    return {
        "schema_version": "issue_intake_scope_fidelity_v1",
        "fix": "FIX 185",
        "intended_goal": envelope.intended_goal,
        "expected_files": list(envelope.expected_files),
        "out_of_scope_constraints": list(envelope.out_of_scope_constraints),
        "explicit_bounded_scope": envelope.explicit_bounded_scope,
        "scope_confidence": envelope.scope_confidence,
        "forbidden_file_prefixes": list(envelope.forbidden_file_prefixes),
        "issue_title": envelope.issue_title,
        "feeds_fix_184_expected_targets": True,
        "plan_authority_enabled": False,
    }


def _plan_goal_divergence(
    *,
    envelope: IssueScopeFidelityEnvelope,
    plan_goal: str,
) -> tuple[bool, str]:
    goal = (plan_goal or "").strip()
    issue_text = f"{envelope.issue_title}\n{envelope.issue_body_excerpt}".lower()
    goal_lower = goal.lower()

    if re.search(WORKFLOW_REFRAME_GOAL_RX, goal_lower, re.I) and not _WORKFLOW_HEURISTIC_RX.search(issue_text):
        return True, "plan_goal_reframes_issue_as_workflow_fix"

    if _DOGFOOD_RX.search(issue_text):
        if "pilot execution log" in issue_text and "pilot execution log" not in goal_lower:
            if "dogfood" not in goal_lower and envelope.intended_goal.lower() not in goal_lower:
                return True, "plan_goal_missing_dogfood_pilot_execution_log_scope"

    if envelope.intended_goal and envelope.intended_goal.lower() not in goal_lower:
        title_fragment = envelope.issue_title.lower()[:40]
        if title_fragment and title_fragment not in goal_lower and envelope.explicit_bounded_scope:
            return True, "plan_goal_diverges_from_issue_title_scope"

    return False, ""


def _forbidden_files_in_plan(*, envelope: IssueScopeFidelityEnvelope, files: list[str]) -> list[str]:
    forbidden: list[str] = []
    for path in files:
        if envelope.expected_files and path not in envelope.expected_files:
            for prefix in envelope.forbidden_file_prefixes:
                if path.startswith(prefix) and path not in forbidden:
                    forbidden.append(path)
                    break
        if envelope.explicit_bounded_scope and envelope.expected_files and path not in envelope.expected_files:
            for prefix, _ in FORBIDDEN_OUT_OF_SCOPE_PREFIXES:
                if path.startswith(prefix) and path not in forbidden:
                    forbidden.append(path)
                    break
    return forbidden


def assess_plan_scope_fidelity(*, plan: dict[str, Any]) -> PlanScopeFidelityAssessment:
    envelope_payload = plan.get("issue_intake_scope_fidelity") or {}
    governed = plan.get("governed_plan") or {}
    plan_goal = str(governed.get("goal") or "")
    affected = [str(p) for p in list(plan.get("affected_files") or []) if p]

    envelope = IssueScopeFidelityEnvelope(
        intended_goal=str(envelope_payload.get("intended_goal") or plan.get("issue_title") or ""),
        expected_files=list(envelope_payload.get("expected_files") or []),
        out_of_scope_constraints=list(envelope_payload.get("out_of_scope_constraints") or []),
        explicit_bounded_scope=bool(envelope_payload.get("explicit_bounded_scope")),
        scope_confidence=str(envelope_payload.get("scope_confidence") or "low"),
        issue_title=str(plan.get("issue_title") or ""),
        issue_body_excerpt=str(plan.get("issue_body") or "")[:500],
        forbidden_file_prefixes=list(envelope_payload.get("forbidden_file_prefixes") or []),
    )

    diverged, divergence_detail = _plan_goal_divergence(envelope=envelope, plan_goal=plan_goal)
    forbidden_files = _forbidden_files_in_plan(envelope=envelope, files=affected)

    score = 100
    reasons: list[str] = []
    if diverged:
        score -= 45
        reasons.append("plan_goal_diverges_from_issue_scope")
    if forbidden_files:
        score -= min(40, len(forbidden_files) * 15)
        reasons.append("plan_files_violate_out_of_scope")
    if envelope.expected_files and affected:
        missing = [p for p in envelope.expected_files if p not in affected]
        if missing:
            score -= min(25, len(missing) * 10)
            reasons.append("expected_issue_files_missing_from_plan")
    if envelope.scope_confidence == "low":
        score -= 10
        reasons.append("issue_scope_indeterminate")

    score = max(0, min(100, score))
    escalation = score < FIDELITY_ESCALATION_THRESHOLD or bool(reasons)

    ok = not diverged and not forbidden_files and score >= FIDELITY_ESCALATION_THRESHOLD
    detail = "Plan scope fidelity preserved from GitHub issue."
    if diverged:
        detail = f"Plan goal diverges from issue scope: {divergence_detail}."
    elif forbidden_files:
        detail = f"Plan includes out-of-scope files: {', '.join(forbidden_files[:3])}."

    return PlanScopeFidelityAssessment(
        ok=ok,
        fidelity_score=score,
        escalation_required=escalation,
        escalation_reasons=reasons,
        plan_goal_divergence=diverged,
        plan_goal_divergence_detail=divergence_detail,
        forbidden_files_in_plan=forbidden_files,
        detail=detail,
    )


def expected_targets_for_fix_184(*, plan: dict[str, Any]) -> list[str]:
    envelope = plan.get("issue_intake_scope_fidelity") or {}
    expected = list(envelope.get("expected_files") or [])
    if expected:
        return expected
    return _extract_paths_from_text(str(plan.get("issue_body") or ""))


def build_issue_intake_scope_fidelity_snapshot(*, session_id: str) -> dict[str, Any]:
    """Readonly FIX 185 snapshot for Mission Control / manual gate."""
    from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline

    sid = (session_id or "default").strip()[:64] or "default"
    timeline = build_software_delivery_timeline(session_id=sid)
    plan = dict(timeline.get("plan") or {})
    if not plan:
        return {
            "ok": False,
            "session_id": sid,
            "fix": "FIX 185",
            "read_only": True,
            "blockers": ["no_issue_plan"],
            "detail": "Issue intake scope fidelity unavailable — analyze a GitHub issue and create a plan first.",
        }

    assessment = assess_plan_scope_fidelity(plan=plan)
    envelope = dict(plan.get("issue_intake_scope_fidelity") or {})
    return {
        "ok": True,
        "session_id": sid,
        "fix": "FIX 185",
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": False,
        "plan_authority_enabled": False,
        "issue_intake_scope_fidelity": envelope,
        "assessment": {
            "fidelity_score": assessment.fidelity_score,
            "escalation_required": assessment.escalation_required,
            "escalation_reasons": list(assessment.escalation_reasons),
            "plan_goal_divergence": assessment.plan_goal_divergence,
            "plan_goal_divergence_detail": assessment.plan_goal_divergence_detail,
            "forbidden_files_in_plan": list(assessment.forbidden_files_in_plan),
            "detail": assessment.detail,
        },
        "feeds_fix_184_expected_targets": True,
        "expected_targets_for_fix_184": expected_targets_for_fix_184(plan=plan),
        "detail": assessment.detail or "Issue intake scope fidelity composed from frozen issue plan.",
    }
