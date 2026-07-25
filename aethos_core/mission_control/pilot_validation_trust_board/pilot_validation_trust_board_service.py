# SPDX-License-Identifier: Apache-2.0
"""FIX 183 — pilot validation and trust board (composes FIX 181 audits)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_183_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
    PILOT_TERMINAL_STAGE as PILOT_HARNESS_TERMINAL_STAGE,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_pilot_run_audits,
)
from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.job_replay.job_replay_deep_link import (
    replay_link_key,
    timeline_link_ref,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_contract import (
    AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183,
    DIRECT_EXECUTION_PERFORMED_FIX_183,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183,
    EXECUTION_PERFORMED_FIX_183,
    FORBIDDEN_VALIDATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_183,
    GOVERNANCE_MUTATION_PERFORMED_FIX_183,
    HIDDEN_PILOT_REEXECUTION_PERFORMED_FIX_183,
    MUTATION_PERFORMED_FIX_183,
    PILOT_REEXECUTION_PERFORMED_FIX_183,
    PILOT_TERMINAL_STAGE_FIX_183,
    PILOT_VALIDATION_TRUST_BOARD_FIX,
    PILOT_VALIDATION_TRUST_BOARD_INVARIANT,
    PILOT_VALIDATION_TRUST_BOARD_ORIGIN,
    PILOT_VALIDATION_TRUST_BOARD_PRINCIPLES,
    PILOT_VALIDATION_TRUST_BOARD_SCHEMA_VERSION,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
    VALIDATION_COMPOSES_AUDITS_ONLY_FIX_183,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_store import (
    list_pilot_validation_trust_board_records,
)
from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
from aethos_core.software_delivery.github_pr_open_contract import GITHUB_PR_OPEN_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_preflight_contract import GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_APPROVAL_PHRASE,
    MUTATION_PREVIEW_ACK_PHRASE,
)
from aethos_core.software_delivery.workspace_application_contract import WORKSPACE_APPLY_APPROVAL_PHRASE
from aethos_core.software_delivery.software_delivery_phase_2_contract import SOFTWARE_DELIVERY_LOOP_ORDER

_APPROVAL_PHRASES: tuple[str, ...] = (
    PLANNING_APPROVAL_PHRASE,
    BRANCH_CREATE_APPROVAL_PHRASE,
    PATCH_PROPOSAL_APPROVAL_PHRASE,
    WORKSPACE_APPLY_APPROVAL_PHRASE,
    GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
    BRANCH_PUSH_APPROVAL_PHRASE,
    MUTATION_PREVIEW_ACK_PHRASE,
    GITHUB_PR_OPEN_APPROVAL_PHRASE,
)

_REENGAGEMENT_HINTS: tuple[str, ...] = (
    "approval_phrase_required",
    "planning_approval_phrase_required",
    "stage_blocked",
    "partial",
    "rejected",
    "re-engagement",
)


@dataclass(frozen=True)
class PilotValidationTrustBoardResult:
    ok: bool
    session_id: str
    pilot_validation_trust_board: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _parse_timestamp(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _select_focus_audit(audits: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not audits:
        return None
    complete = [a for a in audits if str(a.get("outcome") or "") == "complete"]
    pool = complete or audits
    return max(pool, key=lambda a: _parse_timestamp(a.get("recorded_at")))


def _count_approval_touches(chat_steps: list[dict[str, Any]]) -> int:
    count = 0
    for step in chat_steps:
        message = str(step.get("chat_message") or "")
        if any(phrase in message for phrase in _APPROVAL_PHRASES):
            count += 1
    return count


def _count_re_engagements(audits: list[dict[str, Any]], chat_steps: list[dict[str, Any]]) -> int:
    partial_runs = sum(1 for a in audits if str(a.get("outcome") or "") == "partial")
    reply_hits = 0
    for step in chat_steps:
        blob = f"{step.get('chat_message') or ''} {step.get('reply_excerpt') or ''}".lower()
        if any(hint in blob for hint in _REENGAGEMENT_HINTS):
            reply_hits += 1
    return partial_runs + reply_hits


def _manual_intervention_points(audits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for audit in audits:
        for blocker in audit.get("blockers") or []:
            points.append(
                {
                    "intervention_id": f"blocker-{audit.get('audit_id')}-{len(points) + 1}",
                    "audit_id": audit.get("audit_id"),
                    "kind": "stage_blocker",
                    "detail": str(blocker),
                    "recorded_at": audit.get("recorded_at"),
                    "read_only": True,
                }
            )
        if str(audit.get("outcome") or "") == "partial" and not audit.get("blockers"):
            points.append(
                {
                    "intervention_id": f"partial-{audit.get('audit_id')}",
                    "audit_id": audit.get("audit_id"),
                    "kind": "partial_pilot_run",
                    "detail": "Pilot run stopped before terminal stage — operator re-engagement required.",
                    "recorded_at": audit.get("recorded_at"),
                    "read_only": True,
                }
            )
    return points


def _elapsed_seconds(audits: list[dict[str, Any]]) -> float:
    if not audits:
        return 0.0
    stamps = [_parse_timestamp(a.get("recorded_at")) for a in audits]
    stamps = [s for s in stamps if s > 0]
    if len(stamps) < 2:
        return 0.0
    return round(max(stamps) - min(stamps), 2)


def _human_effort_score(
    *,
    approval_count: int,
    re_engagement_count: int,
    manual_intervention_count: int,
    chat_step_count: int,
    partial_run_count: int,
) -> tuple[int, str]:
  # Lower operator burden → higher score (0–100, higher is better for trust).
    penalty = (
        approval_count * 4
        + re_engagement_count * 8
        + manual_intervention_count * 10
        + max(0, chat_step_count - 12) * 2
        + partial_run_count * 12
    )
    score = max(0, min(100, 100 - penalty))
    if score >= 75:
        label = "low_effort"
    elif score >= 50:
        label = "moderate_effort"
    else:
        label = "high_effort"
    return score, label


def _issue_risk_tier(*, timeline: dict[str, Any]) -> str:
    plan = timeline.get("plan") or {}
    risk = plan.get("risk_assessment") or {}
    tier = str(risk.get("risk_tier") or "").strip()
    if tier:
        return tier
    blast = str(plan.get("blast_radius") or "").strip()
    if blast:
        return blast
    return "unknown_bounded"


def _evidence_completeness(*, session_id: str, focus_report: dict[str, Any]) -> dict[str, Any]:
    bundle = build_evidence_bundle(session_id=session_id)
    sections = (bundle.bundle.get("sections") or {}) if bundle.ok else {}
    required = ("timeline", "lane_drilldowns", "jobs", "lifecycle")
    present = [key for key in required if key in sections]
    completeness = round((len(present) / len(required)) * 100) if required else 0
    return {
        "capture_id": "validation-evidence-completeness",
        "bundle_ok": bundle.ok,
        "evidence_bundle_ok": bool(focus_report.get("evidence_bundle_ok")),
        "section_count": len(sections),
        "required_sections_present": present,
        "completeness_percent": completeness,
        "replay_available": bundle.ok,
        "read_only": True,
    }


def _trust_recommendation(
    *,
    outcome: str,
    stages_satisfied: list[str],
    stages_pending: list[str],
    approval_count: int,
    re_engagement_count: int,
    human_effort_score: int,
    evidence_completeness_percent: int,
    railway_detected: bool,
) -> tuple[str, str]:
    terminal = PILOT_TERMINAL_STAGE_FIX_183
    reached_terminal = terminal in stages_satisfied and not stages_pending

    if railway_detected:
        return "no", "Railway coupling detected during pilot — do not trust larger issues without remediation."

    if outcome == "complete" and reached_terminal:
        if human_effort_score >= 70 and evidence_completeness_percent >= 75 and re_engagement_count <= 2:
            return (
                "yes",
                "Pilot reached PR Open with acceptable operator effort and complete evidence.",
            )
        return (
            "conditional",
            "Pilot reached PR Open but operator friction or evidence gaps warrant review before larger issues.",
        )

    if stages_satisfied and len(stages_satisfied) >= len(SOFTWARE_DELIVERY_LOOP_ORDER) // 2:
        return (
            "conditional",
            f"Pilot stopped at `{stages_pending[0] if stages_pending else 'unknown'}` — partial loop evidence only.",
        )

    return (
        "no",
        "Pilot did not reach PR Open — do not trust larger issues until the loop completes.",
    )


def _pilot_harness_upstream_read(*, harness: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "read_id": "fix-181-pilot-harness-read",
            "upstream_fix": "FIX 181",
            "repo_issue": harness.get("repo_issue"),
            "terminal_stage": harness.get("terminal_stage"),
            "pilot_record_count": harness.get("pilot_record_count"),
            "pilot_run_audits": (harness.get("sources") or {}).get("pilot_run_audits"),
            "read_only": True,
            "recomputed_by_fix_183": False,
        }
    ]


def _pilot_audit_composition(*, audits: list[dict[str, Any]], focus_audit: dict[str, Any] | None) -> list[dict[str, Any]]:
    return [
        {
            "composition_id": "fix-181-audit-composition",
            "audit_count": len(audits),
            "focus_audit_id": focus_audit.get("audit_id") if focus_audit else None,
            "focus_outcome": focus_audit.get("outcome") if focus_audit else None,
            "validation_composes_audits_only": VALIDATION_COMPOSES_AUDITS_ONLY_FIX_183,
            "pilot_reexecution_performed": False,
            "read_only": True,
        }
    ]


def build_pilot_validation_trust_board(*, session_id: str) -> PilotValidationTrustBoardResult:
    sid = (session_id or "default").strip()[:64] or "default"
    exported_at = _exported_at()

    harness_result = build_end_to_end_repo_development_pilot_harness(session_id=sid)
    harness = harness_result.end_to_end_repo_development_pilot_harness if harness_result.ok else {}

    plan_id = str(harness.get("plan_id") or "") or None
    correlation_id = str(harness.get("correlation_id") or "") or None
    records = list_pilot_validation_trust_board_records(session_id=sid, plan_id=plan_id)
    audits = list_pilot_run_audits(session_id=sid)
    focus_audit = _select_focus_audit(audits)

    blockers: list[str] = []
    if not audits:
        blockers.append("no_pilot_run_audits")

    all_chat_steps: list[dict[str, Any]] = []
    for audit in audits:
        all_chat_steps.extend(audit.get("chat_steps") or [])

    focus_report = dict(focus_audit.get("pilot_report") or {}) if focus_audit else {}
    outcome = str(focus_audit.get("outcome") or "none") if focus_audit else "none"
    repo_issue = str(
        (focus_audit or {}).get("repo_issue") or harness.get("repo_issue") or "none"
    )
    stages_satisfied = list(focus_report.get("stages_satisfied") or [])
    stages_pending = list(focus_report.get("stages_pending") or [])
    stage_stopped_at = stages_pending[0] if stages_pending else None
    if outcome == "complete" and not stages_pending:
        stage_stopped_at = PILOT_TERMINAL_STAGE_FIX_183

    approval_count = _count_approval_touches(all_chat_steps)
    re_engagement_count = _count_re_engagements(audits, all_chat_steps)
    manual_points = _manual_intervention_points(audits)
    elapsed = _elapsed_seconds(audits)
    partial_run_count = sum(1 for a in audits if str(a.get("outcome") or "") == "partial")

    human_effort_score, human_effort_label = _human_effort_score(
        approval_count=approval_count,
        re_engagement_count=re_engagement_count,
        manual_intervention_count=len(manual_points),
        chat_step_count=len(all_chat_steps),
        partial_run_count=partial_run_count,
    )

    timeline = build_software_delivery_timeline(session_id=sid)
    issue_risk_tier = _issue_risk_tier(timeline=timeline)
    evidence = _evidence_completeness(session_id=sid, focus_report=focus_report)
    railway_detected = any(bool(a.get("railway_coupling_detected")) for a in audits)

    trust_value, trust_rationale = _trust_recommendation(
        outcome=outcome,
        stages_satisfied=stages_satisfied,
        stages_pending=stages_pending,
        approval_count=approval_count,
        re_engagement_count=re_engagement_count,
        human_effort_score=human_effort_score,
        evidence_completeness_percent=int(evidence.get("completeness_percent") or 0),
        railway_detected=railway_detected,
    )

    timeline_ref = timeline_link_ref(
        lane="software_delivery",
        action="pilot_validation_trust_board",
        timestamp=exported_at,
    )
    replay_key = replay_link_key(
        source=PILOT_VALIDATION_TRUST_BOARD_ORIGIN,
        lane="software_delivery",
        action="pilot_validation_trust_board",
        timestamp=exported_at,
        anchor=plan_id or sid,
    )

    sections = {
        "pilot_harness_upstream_read": _pilot_harness_upstream_read(harness=harness),
        "pilot_audit_composition": _pilot_audit_composition(audits=audits, focus_audit=focus_audit),
        "stage_completion_summary": [
            {
                "summary_id": "pilot-stage-completion",
                "stages_completed": stages_satisfied,
                "stages_pending": stages_pending,
                "stage_stopped_at": stage_stopped_at,
                "terminal_stage": PILOT_HARNESS_TERMINAL_STAGE,
                "pilot_outcome": outcome,
                "read_only": True,
            }
        ],
        "approval_friction_metrics": [
            {
                "metric_id": "approval-count",
                "approval_count": approval_count,
                "chat_step_count": len(all_chat_steps),
                "approval_phrases_preserved": True,
                "read_only": True,
            }
        ],
        "re_engagement_metrics": [
            {
                "metric_id": "re-engagement-count",
                "re_engagement_count": re_engagement_count,
                "partial_pilot_run_count": partial_run_count,
                "read_only": True,
            }
        ],
        "manual_intervention_points": manual_points or [
            {
                "intervention_id": "none",
                "detail": "No manual intervention points recorded in pilot audits.",
                "read_only": True,
            }
        ],
        "elapsed_time_capture": [
            {
                "capture_id": "pilot-elapsed-time",
                "elapsed_seconds": elapsed,
                "audit_count": len(audits),
                "read_only": True,
            }
        ],
        "evidence_completeness_capture": [evidence],
        "issue_risk_tier": [
            {
                "risk_id": "pilot-issue-risk-tier",
                "issue_risk_tier": issue_risk_tier,
                "repo_issue": repo_issue,
                "read_only": True,
            }
        ],
        "human_effort_scoring": [
            {
                "score_id": "operator-human-effort",
                "human_effort_score": human_effort_score,
                "human_effort_label": human_effort_label,
                "approval_count": approval_count,
                "re_engagement_count": re_engagement_count,
                "manual_intervention_count": len(manual_points),
                "read_only": True,
            }
        ],
        "trust_recommendation": [
            {
                "recommendation_id": "pilot-trust-recommendation",
                "trust_recommendation": trust_value,
                "trust_rationale": trust_rationale,
                "read_only": True,
            }
        ],
        "audit_replay_linkage_at_validation": [
            {
                "link_id": "validation-audit-replay",
                "timeline_link_ref": timeline_ref,
                "replay_link_key": replay_key,
                "focus_audit_id": focus_audit.get("audit_id") if focus_audit else None,
                "read_only": True,
            }
        ],
        "forbidden_validation_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_VALIDATION_ACTIONS
        ],
        "validation_integrity_scoring": [
            {
                "score_id": "pilot-validation-integrity",
                "integrity_score": min(
                    100,
                    20
                    + (30 if audits else 0)
                    + (25 if outcome == "complete" else 0)
                    + (15 if evidence.get("bundle_ok") else 0)
                    + (10 if trust_value == "yes" else 5 if trust_value == "conditional" else 0),
                ),
                "validation_composes_audits_only": True,
                "pilot_reexecution_performed": False,
                "read_only": True,
            }
        ],
    }

    pilot_validation_trust_board: dict[str, Any] = {
        "schema_version": PILOT_VALIDATION_TRUST_BOARD_SCHEMA_VERSION,
        "fix": PILOT_VALIDATION_TRUST_BOARD_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_183,
        "execution_performed": EXECUTION_PERFORMED_FIX_183,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_183,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_183,
        "autonomous_validation_execution_enabled": AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183,
        "hidden_pilot_reexecution_performed": HIDDEN_PILOT_REEXECUTION_PERFORMED_FIX_183,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_183,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_183,
        "validation_composes_audits_only": VALIDATION_COMPOSES_AUDITS_ONLY_FIX_183,
        "invariant": PILOT_VALIDATION_TRUST_BOARD_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "validation_record_count": len(records),
        "repo_issue": repo_issue,
        "pilot_audit_count": len(audits),
        "focus_audit_id": focus_audit.get("audit_id") if focus_audit else None,
        "pilot_outcome": outcome,
        "trust_recommendation": trust_value,
        "human_effort_score": human_effort_score,
        "approval_count": approval_count,
        "re_engagement_count": re_engagement_count,
        "elapsed_seconds": elapsed,
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_181_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_181),
        },
        "fix_183_certification_requirements": list(FIX_183_CERTIFICATION_REQUIREMENTS),
        "pilot_validation_trust_board_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in PILOT_VALIDATION_TRUST_BOARD_PRINCIPLES
        ],
        "sources": {
            "composes_end_to_end_repo_development_pilot_harness": harness_result.ok,
            "end_to_end_repo_development_pilot_harness_fix": "FIX 181",
            "pilot_run_audits": len(audits),
            "validation_records": len(records),
        },
    }

    ok = bool(audits) and not blockers
    return PilotValidationTrustBoardResult(
        ok=ok,
        session_id=sid,
        pilot_validation_trust_board=pilot_validation_trust_board,
        blockers=blockers,
        detail="Pilot validation trust board composed from FIX 181 audits (validation ≠ re-execution)."
        if ok
        else "Pilot validation unavailable — pilot run audits required.",
    )
