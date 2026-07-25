# SPDX-License-Identifier: Apache-2.0
"""FIX 184 — issue intent alignment and patch target validation service."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_184_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_contract import (
    ALIGNMENT_ESCALATION_THRESHOLD,
    ALIGNMENT_VALIDATION_PERFORMED_FIX_184,
    AUTONOMOUS_AUTHORITY_ENABLED_FIX_184,
    AUTONOMOUS_FILE_SELECTION_OVERRIDE_ENABLED_FIX_184,
    AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_184,
    DIRECT_EXECUTION_PERFORMED_FIX_184,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184,
    EXECUTION_PERFORMED_FIX_184,
    FORBIDDEN_ALIGNMENT_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_184,
    GOVERNANCE_MUTATION_PERFORMED_FIX_184,
    ISSUE_INTENT_ALIGNMENT_FIX,
    ISSUE_INTENT_ALIGNMENT_INVARIANT,
    ISSUE_INTENT_ALIGNMENT_ORIGIN,
    ISSUE_INTENT_ALIGNMENT_PRINCIPLES,
    ISSUE_INTENT_ALIGNMENT_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_184,
    PATCH_EXECUTION_PERFORMED_FIX_184,
    UNRELATED_SUBSYSTEM_PREFIXES,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    list_issue_intent_alignment_records,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import (
    replay_link_key,
    timeline_link_ref,
)
from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline

_PATH_RX = re.compile(
    r"`([^`\n]+\.[A-Za-z0-9]+)`|(?:^|\s)((?:[\w.-]+/)+[\w.-]+\.[A-Za-z0-9]+)",
    re.MULTILINE,
)
_OUT_OF_SCOPE_RX = re.compile(r"(?i)(?:out\s+of\s+scope|not\s+in\s+scope)[:\s]+(.+?)(?:\n\n|\Z)", re.S)


@dataclass(frozen=True)
class IssueIntentAlignmentResult:
    ok: bool
    session_id: str
    issue_intent_alignment: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class AlignmentAssessment:
    alignment_score: int
    target_validation_status: str
    patch_purpose_status: str
    authorization_envelope_status: str
    escalation_required: bool
    escalation_reasons: list[str]
    expected_targets: list[str]
    actual_targets: list[str]
    unexpected_files: list[str]
    missing_expected_files: list[str]
    unrelated_findings: list[dict[str, Any]]
    rationale: str
    intended_purpose: str
    intended_subsystem: str
    expected_blast_radius: str


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_path(path: str) -> str:
    return (path or "").strip().replace("\\", "/").lstrip("./")


def _extract_paths_from_text(text: str) -> list[str]:
    found: list[str] = []
    for match in _PATH_RX.finditer(text or ""):
        candidate = _normalize_path(match.group(1) or match.group(2) or "")
        if candidate and candidate not in found:
            found.append(candidate)
    return found


def _issue_scope_text(plan: dict[str, Any]) -> str:
    governed = plan.get("governed_plan") or {}
    chunks = [
        str(plan.get("issue_title") or ""),
        str(plan.get("issue_body") or ""),
        str(governed.get("problem_summary") or ""),
        str(governed.get("goal") or ""),
        str(governed.get("scope") or ""),
        str(plan.get("blast_radius") or ""),
    ]
    return "\n".join(c for c in chunks if c.strip())


def _infer_subsystem(paths: list[str]) -> str:
    if not paths:
        return "indeterminate"
    prefixes: dict[str, int] = {}
    for path in paths:
        if path.startswith("docs/"):
            prefixes["documentation"] = prefixes.get("documentation", 0) + 1
        elif path.startswith(".github/workflows/"):
            prefixes["workflow"] = prefixes.get("workflow", 0) + 1
        elif path.startswith("aethos_core/"):
            prefixes["core_runtime"] = prefixes.get("core_runtime", 0) + 1
        elif path.startswith("web/"):
            prefixes["web_ui"] = prefixes.get("web_ui", 0) + 1
        else:
            prefixes["mixed"] = prefixes.get("mixed", 0) + 1
    return max(prefixes, key=prefixes.get)


def _infer_blast_radius(paths: list[str]) -> str:
    count = len(paths)
    if count == 0:
        return "indeterminate"
    if count == 1 and all(p.startswith("docs/") for p in paths):
        return "single_documentation_file"
    if count <= 3 and all(p.startswith("docs/") for p in paths):
        return "bounded_documentation"
    if count <= 3:
        return "small_multi_file"
    return "expanded_multi_file"


def extract_issue_scope(*, plan: dict[str, Any]) -> dict[str, Any]:
    from aethos_core.software_delivery.issue_intake_scope_fidelity_service import (
        expected_targets_for_fix_184,
    )

    scope_text = _issue_scope_text(plan)
    fidelity_expected = expected_targets_for_fix_184(plan=plan)
    if fidelity_expected:
        expected = list(fidelity_expected)
    else:
        expected = list(
            dict.fromkeys(_extract_paths_from_text(scope_text) + list(plan.get("affected_files") or []))
        )
    expected = [_normalize_path(p) for p in expected if p]
    out_of_scope_match = _OUT_OF_SCOPE_RX.search(scope_text)
    out_of_scope = (out_of_scope_match.group(1).strip() if out_of_scope_match else "")[:500]
    purpose = str((plan.get("governed_plan") or {}).get("goal") or plan.get("issue_title") or "").strip()
    return {
        "expected_targets": expected,
        "intended_purpose": purpose or "indeterminate",
        "intended_subsystem": _infer_subsystem(expected),
        "expected_blast_radius": _infer_blast_radius(expected),
        "out_of_scope_statement": out_of_scope or None,
        "scope_confidence": "high" if expected else "low",
    }


def collect_actual_targets(*, timeline: dict[str, Any]) -> list[str]:
    proposal = timeline.get("patch_proposal") or {}
    proposed = list(proposal.get("proposed_files") or [])
    if proposed:
        return [_normalize_path(p) for p in proposed if p]
    plan = timeline.get("plan") or {}
    return [_normalize_path(p) for p in list(plan.get("affected_files") or []) if p]


def detect_unrelated_changes(
    *,
    expected_targets: list[str],
    actual_targets: list[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    expected_subsystem = _infer_subsystem(expected_targets)
    for path in actual_targets:
        for prefix, label in UNRELATED_SUBSYSTEM_PREFIXES:
            if path.startswith(prefix):
                findings.append(
                    {
                        "finding_id": f"unrelated-{label}-{path.replace('/', '-')}",
                        "path": path,
                        "category": label,
                        "detail": f"Patch target `{path}` is a sensitive subsystem file not typical for `{expected_subsystem}` scope.",
                        "read_only": True,
                    }
                )
                break
        if expected_subsystem == "documentation" and not path.startswith("docs/"):
            findings.append(
                {
                    "finding_id": f"unrelated-non-doc-{path.replace('/', '-')}",
                    "path": path,
                    "category": "non_documentation_target",
                    "detail": f"Issue scope appears documentation-only but patch target `{path}` is outside docs/.",
                    "read_only": True,
                }
            )
    return findings


def compute_alignment_assessment(
    *,
    plan: dict[str, Any],
    timeline: dict[str, Any],
) -> AlignmentAssessment:
    scope = extract_issue_scope(plan=plan)
    expected = list(scope["expected_targets"])
    actual = collect_actual_targets(timeline=timeline)
    unrelated = detect_unrelated_changes(expected_targets=expected, actual_targets=actual)

    expected_set = set(expected)
    actual_set = set(actual)
    unexpected = sorted(actual_set - expected_set)
    missing = sorted(expected_set - actual_set)

    proposal = timeline.get("patch_proposal") or {}
    patch_intent = proposal.get("patch_intent") or {}
    patch_summary = str(patch_intent.get("summary") or "").strip()
    issue_purpose = str(scope["intended_purpose"])

    if not expected:
        score = 50 if actual else 0
        status = "indeterminate"
        purpose_status = "indeterminate"
        envelope_status = "indeterminate"
        rationale = "Issue scope could not be confidently determined from plan and issue text."
    elif not actual:
        score = 100
        status = "pre_patch"
        purpose_status = "pre_patch"
        envelope_status = "within_envelope"
        rationale = "Pre-patch validation — awaiting patch file proposal."
    elif actual_set == expected_set:
        score = 100
        status = "aligned"
        purpose_status = "aligned"
        envelope_status = "within_envelope"
        rationale = "All patch targets match expected issue scope."
    elif expected_set & actual_set:
        overlap_ratio = len(expected_set & actual_set) / max(len(actual_set), 1)
        score = max(0, min(100, int(overlap_ratio * 100) - len(unexpected) * 10 - len(unrelated) * 5))
        status = "partially_aligned" if score >= 40 else "misaligned"
        purpose_status = "partially_aligned" if expected_set & actual_set else "misaligned"
        envelope_status = "partially_within_envelope" if len(actual) <= len(expected) + 1 else "exceeds_envelope"
        rationale = (
            f"Partial overlap — {len(expected_set & actual_set)} expected target(s) matched, "
            f"{len(unexpected)} unexpected file(s)."
        )
    else:
        score = 0
        status = "misaligned"
        purpose_status = "misaligned"
        envelope_status = "exceeds_envelope"
        rationale = "No patch targets overlap expected issue scope."

    if unrelated:
        score = max(0, score - min(40, len(unrelated) * 10))
        if status == "aligned":
            status = "partially_aligned"
        rationale = f"{rationale} Unrelated subsystem files detected."

    if patch_summary and issue_purpose and issue_purpose.lower() not in patch_summary.lower():
        if status == "aligned":
            purpose_status = "partially_aligned"
            score = max(0, score - 10)

    escalation_reasons: list[str] = []
    if score < ALIGNMENT_ESCALATION_THRESHOLD:
        escalation_reasons.append("alignment_score_below_threshold")
    if unexpected:
        escalation_reasons.append("unexpected_files_detected")
    if unrelated:
        escalation_reasons.append("unrelated_subsystem_files_detected")
    if envelope_status == "exceeds_envelope":
        escalation_reasons.append("blast_radius_exceeds_authorization_envelope")
    if scope["scope_confidence"] == "low":
        escalation_reasons.append("issue_scope_indeterminate")

    return AlignmentAssessment(
        alignment_score=score,
        target_validation_status=status,
        patch_purpose_status=purpose_status,
        authorization_envelope_status=envelope_status,
        escalation_required=bool(escalation_reasons),
        escalation_reasons=escalation_reasons,
        expected_targets=expected,
        actual_targets=actual,
        unexpected_files=unexpected,
        missing_expected_files=missing,
        unrelated_findings=unrelated,
        rationale=rationale,
        intended_purpose=issue_purpose,
        intended_subsystem=str(scope["intended_subsystem"]),
        expected_blast_radius=str(scope["expected_blast_radius"]),
    )


def intent_alignment_gate_satisfied(*, session_id: str, timeline: dict[str, Any]) -> bool:
    plan = timeline.get("plan") or {}
    plan_id = str(plan.get("plan_id") or "")
    if not plan_id or not timeline.get("branch_context"):
        return True

    proposal = timeline.get("patch_proposal") or {}
    if proposal.get("patch_proposal_approved"):
        return True

    records = list_issue_intent_alignment_records(session_id=session_id, plan_id=plan_id)
    if any(str(r.get("kind") or "") == "alignment_review_acknowledged" for r in records):
        return True

    assessment = compute_alignment_assessment(plan=plan, timeline=timeline)
    if assessment.escalation_required:
        return False
    return (
        assessment.alignment_score >= ALIGNMENT_ESCALATION_THRESHOLD
        and assessment.target_validation_status in {"aligned", "pre_patch"}
    )


def build_issue_intent_alignment(*, session_id: str) -> IssueIntentAlignmentResult:
    sid = (session_id or "default").strip()[:64] or "default"
    exported_at = _exported_at()

    harness_result = build_end_to_end_repo_development_pilot_harness(session_id=sid)
    harness = harness_result.end_to_end_repo_development_pilot_harness if harness_result.ok else {}

    plan_id = str(harness.get("plan_id") or "") or None
    correlation_id = str(harness.get("correlation_id") or "") or None
    records = list_issue_intent_alignment_records(session_id=sid, plan_id=plan_id)
    timeline = build_software_delivery_timeline(session_id=sid)
    plan = timeline.get("plan") or {}

    blockers: list[str] = []
    if not plan:
        blockers.append("no_implementation_plan")

    assessment = compute_alignment_assessment(plan=plan, timeline=timeline)
    scope = extract_issue_scope(plan=plan)
    operator_acknowledged = any(str(r.get("kind") or "") == "alignment_review_acknowledged" for r in records)

    timeline_ref = timeline_link_ref(
        lane="software_delivery",
        action="issue_intent_alignment",
        timestamp=exported_at,
    )
    replay_key = replay_link_key(
        source=ISSUE_INTENT_ALIGNMENT_ORIGIN,
        lane="software_delivery",
        action="issue_intent_alignment",
        timestamp=exported_at,
        anchor=plan_id or sid,
    )

    recommended_review = "Proceed to patch proposal — alignment within threshold."
    if assessment.escalation_required:
        recommended_review = (
            "Human re-engagement recommended before patch proposal. "
            "Review misalignment findings and record `alignment review: <rationale>` when scope is confirmed."
        )
    elif operator_acknowledged:
        recommended_review = "Operator acknowledged alignment review — pilot may proceed when gate satisfied."

    sections = {
        "pilot_harness_upstream_read": [
            {
                "read_id": "fix-181-pilot-harness-read",
                "upstream_fix": "FIX 181",
                "repo_issue": harness.get("repo_issue"),
                "plan_id": plan_id,
                "read_only": True,
            }
        ],
        "issue_scope_extraction": [
            {
                "extraction_id": "issue-scope",
                "expected_targets": assessment.expected_targets,
                "intended_purpose": assessment.intended_purpose,
                "intended_subsystem": assessment.intended_subsystem,
                "expected_blast_radius": assessment.expected_blast_radius,
                "out_of_scope_statement": scope.get("out_of_scope_statement"),
                "scope_confidence": scope.get("scope_confidence"),
                "read_only": True,
            }
        ],
        "patch_target_validation": [
            {
                "validation_id": "patch-targets",
                "expected_targets": assessment.expected_targets,
                "actual_targets": assessment.actual_targets,
                "unexpected_files": assessment.unexpected_files,
                "missing_expected_files": assessment.missing_expected_files,
                "target_validation_status": assessment.target_validation_status,
                "read_only": True,
            }
        ],
        "patch_purpose_validation": [
            {
                "validation_id": "patch-purpose",
                "issue_intent": assessment.intended_purpose,
                "patch_purpose_status": assessment.patch_purpose_status,
                "detail": "Patch purpose compared to issue intent — validation only.",
                "read_only": True,
            }
        ],
        "authorization_envelope_validation": [
            {
                "validation_id": "authorization-envelope",
                "authorization_envelope_status": assessment.authorization_envelope_status,
                "expected_blast_radius": assessment.expected_blast_radius,
                "actual_target_count": len(assessment.actual_targets),
                "autonomous_scope_expansion_enabled": False,
                "read_only": True,
            }
        ],
        "unrelated_change_detection": assessment.unrelated_findings
        or [
            {
                "finding_id": "none",
                "detail": "No unrelated subsystem files detected in current targets.",
                "read_only": True,
            }
        ],
        "alignment_assessment": [
            {
                "assessment_id": "alignment-score",
                "alignment_score": assessment.alignment_score,
                "alignment_threshold": ALIGNMENT_ESCALATION_THRESHOLD,
                "rationale": assessment.rationale,
                "advisory_only": True,
                "read_only": True,
            }
        ],
        "misalignment_findings": [
            {
                "finding_id": f"misalignment-{idx + 1}",
                "path": path,
                "detail": f"Unexpected patch target outside issue scope: `{path}`",
                "read_only": True,
            }
            for idx, path in enumerate(assessment.unexpected_files)
        ]
        or [
            {
                "finding_id": "none",
                "detail": "No misalignment findings — targets match expected scope.",
                "read_only": True,
            }
        ],
        "escalation_rules": [
            {
                "rule_id": "escalation-summary",
                "escalation_required": assessment.escalation_required,
                "escalation_reasons": assessment.escalation_reasons,
                "operator_acknowledged": operator_acknowledged,
                "human_reengagement_required": assessment.escalation_required and not operator_acknowledged,
                "read_only": True,
            }
        ],
        "recommended_review": [
            {
                "review_id": "operator-guidance",
                "guidance": recommended_review,
                "executable": False,
                "read_only": True,
            }
        ],
        "audit_replay_linkage_at_alignment": [
            {
                "link_id": "alignment-audit-replay",
                "timeline_link_ref": timeline_ref,
                "replay_link_key": replay_key,
                "read_only": True,
            }
        ],
        "forbidden_alignment_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_ALIGNMENT_ACTIONS
        ],
        "alignment_integrity_scoring": [
            {
                "score_id": "issue-intent-alignment-integrity",
                "integrity_score": min(
                    100,
                    25
                    + (25 if plan else 0)
                    + (20 if assessment.expected_targets else 0)
                    + (20 if assessment.alignment_score >= ALIGNMENT_ESCALATION_THRESHOLD else 5)
                    + (10 if not assessment.escalation_required else 0),
                ),
                "alignment_validation_performed": True,
                "patch_execution_performed": False,
                "read_only": True,
            }
        ],
    }

    issue_intent_alignment: dict[str, Any] = {
        "schema_version": ISSUE_INTENT_ALIGNMENT_SCHEMA_VERSION,
        "fix": ISSUE_INTENT_ALIGNMENT_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_184,
        "execution_performed": EXECUTION_PERFORMED_FIX_184,
        "patch_execution_performed": PATCH_EXECUTION_PERFORMED_FIX_184,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_184,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184,
        "autonomous_scope_expansion_enabled": AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_184,
        "autonomous_file_selection_override_enabled": AUTONOMOUS_FILE_SELECTION_OVERRIDE_ENABLED_FIX_184,
        "autonomous_authority_enabled": AUTONOMOUS_AUTHORITY_ENABLED_FIX_184,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_184,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_184,
        "alignment_validation_performed": ALIGNMENT_VALIDATION_PERFORMED_FIX_184,
        "invariant": ISSUE_INTENT_ALIGNMENT_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "alignment_record_count": len(records),
        "repo_issue": harness.get("repo_issue"),
        "alignment_score": assessment.alignment_score,
        "target_validation_status": assessment.target_validation_status,
        "escalation_required": assessment.escalation_required,
        "intent_alignment_gate_satisfied": intent_alignment_gate_satisfied(session_id=sid, timeline=timeline),
        "operator_acknowledged": operator_acknowledged,
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {"fix_181_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_181)},
        "fix_184_certification_requirements": list(FIX_184_CERTIFICATION_REQUIREMENTS),
        "issue_intent_alignment_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in ISSUE_INTENT_ALIGNMENT_PRINCIPLES
        ],
        "sources": {
            "composes_end_to_end_repo_development_pilot_harness": harness_result.ok,
            "end_to_end_repo_development_pilot_harness_fix": "FIX 181",
            "alignment_records": len(records),
        },
    }

    ok = bool(plan) and not blockers
    return IssueIntentAlignmentResult(
        ok=ok,
        session_id=sid,
        issue_intent_alignment=issue_intent_alignment,
        blockers=blockers,
        detail="Issue intent alignment assessment assembled (validation ≠ patch execution)."
        if ok
        else "Issue intent alignment unavailable — implementation plan required.",
    )
