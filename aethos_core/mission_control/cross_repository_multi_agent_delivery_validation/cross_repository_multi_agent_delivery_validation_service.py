# SPDX-License-Identifier: Apache-2.0
"""FIX 191 — cross-repository multi-agent delivery validation service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_191_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
    CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_FIX,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_INVARIANT,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_PRINCIPLES,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_SCHEMA_VERSION,
    DEPLOY_AUTHORITY_FIX_191,
    FORBIDDEN_VALIDATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_191,
    GOVERNANCE_MUTATION_PERFORMED_FIX_191,
    MERGE_AUTHORITY_FIX_191,
    MUTATION_PERFORMED_FIX_191,
    EXECUTION_PERFORMED_FIX_191,
    PHASE_1_REPOSITORY,
    PILOT_VALIDATION_MILESTONES,
    PROVIDER_AUTHORITY_FIX_191,
    RAILWAY_AUTHORITY_FIX_191,
    REPOSITORY_DISPLAY_NAMES,
    REPOSITORY_PILOT_SESSIONS,
    TRUST_TRANSFER_ENABLED_FIX_191,
    VALIDATION_COMPOSES_ARTIFACTS_ONLY_FIX_191,
    VALIDATION_REPOSITORIES,
    VALIDATION_TRUST_STATES,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_store import (
    list_cross_repository_multi_agent_delivery_validation_records,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_contract import (
    TRUST_RECOMMENDATION_FIX_186,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_pilot_run_audits,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    PHASE_2_REPOSITORY_ORDER,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    list_issue_intent_alignment_records,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    PILOTOS_UI_REPOSITORY,
)
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
    ATLAS_TRADER_REPOSITORY,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
    NEXORA_REPOSITORY,
)


@dataclass(frozen=True)
class CrossRepositoryMultiAgentDeliveryValidationResult:
    ok: bool
    session_id: str
    cross_repository_multi_agent_delivery_validation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _latest_audit(session_id: str, *, repository: str) -> dict[str, Any] | None:
    for audit in list_pilot_run_audits(session_id=session_id, limit=20):
        issue = str(audit.get("repo_issue") or "")
        if repository.lower() in issue.lower() or session_id in str(audit.get("session_id") or ""):
            return audit
    return None


def _pilot_complete(audit: dict[str, Any] | None, *, require_pr_open: bool = False) -> bool:
    if not audit:
        return False
    outcome = str(audit.get("outcome") or "")
    report = dict(audit.get("pilot_report") or {})
    stages = list(report.get("stages_satisfied") or audit.get("stages_completed") or [])
    if require_pr_open:
        return outcome == "complete" and "pr_open" in stages
    return outcome == "complete" or bool(stages)


def _pilot2_alignment_demonstrated(audit: dict[str, Any] | None, session_id: str) -> bool:
    if not audit:
        return False
    if str(audit.get("outcome") or "") == "partial":
        blockers = audit.get("blockers") or []
        if any("intent_alignment" in str(b) for b in blockers):
            return True
    if list_issue_intent_alignment_records(session_id=session_id):
        return True
    report = dict(audit.get("pilot_report") or {})
    return "intent_alignment" in list(report.get("stages_satisfied") or [])


def _alignment_score_for_sessions(sessions: tuple[str, ...]) -> int | None:
    scores: list[int] = []
    for sid in sessions:
        for record in list_issue_intent_alignment_records(session_id=sid):
            meta = record.get("metadata") or {}
            if meta.get("alignment_score") is not None:
                scores.append(int(meta.get("alignment_score")))
            elif record.get("alignment_score") is not None:
                scores.append(int(record.get("alignment_score")))
    return max(scores) if scores else None


def _human_intervention_count(sessions: tuple[str, ...]) -> int:
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_store import (
        list_agent_execution_quality_throughput_metrics_records,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        list_bounded_multi_agent_delivery_execution_records,
    )

    intervention_kinds = {
        "human_intervention_note",
        "execution_note",
        "metrics_observation",
        "throughput_note",
    }
    count = 0
    for sid in sessions:
        metrics_records = list_agent_execution_quality_throughput_metrics_records(session_id=sid)
        execution_records = list_bounded_multi_agent_delivery_execution_records(session_id=sid)
        for record in metrics_records + execution_records:
            if str(record.get("author") or "") == "operator" and str(record.get("kind") or "") in intervention_kinds:
                count += 1
    return count


def _agent_metrics_for_session(session_id: str) -> dict[str, Any] | None:
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        list_agent_execution_receipts,
    )

    receipts = list_agent_execution_receipts(session_id=session_id, plan_id=None)
    if not receipts:
        return None

    completed = 0
    for receipt in receipts:
        meta = dict(receipt.get("metadata") or {})
        if meta.get("work_performed") or str(meta.get("status") or "") == "completed":
            completed += 1
    completion_rate = (completed / len(receipts) * 100) if receipts else 0.0
    throughput = max(0.0, min(100.0, round(completion_rate * 0.6, 1)))

    return {
        "throughput_score": throughput,
        "throughput_label": "high"
        if throughput >= 75
        else "moderate"
        if throughput >= 50
        else "low"
        if throughput > 0
        else "unmeasured",
        "package_completion_rate_percent": round(completion_rate, 1),
        "execution_receipt_count": len(receipts),
        "composed_from_fix_189_receipts_only": True,
        "read_only": True,
    }


def _derive_throughput_score(
    *,
    pilot_1_complete: bool,
    pilot_2_complete: bool,
    pilot_3_complete: bool,
    alignment_score: int | None,
    human_intervention_count: int,
    agent_throughput: float | None,
    pr_open_success: bool,
) -> float | None:
    if agent_throughput is not None and float(agent_throughput) > 0:
        return float(agent_throughput)
    if not (pilot_1_complete or pilot_2_complete or pilot_3_complete):
        return None
    score = 15.0
    if pilot_3_complete:
        score += 45.0
    elif pilot_2_complete:
        score += 28.0
    elif pilot_1_complete:
        score += 12.0
    if alignment_score is not None:
        score += alignment_score * 0.2
    if pr_open_success:
        score += 8.0
    score -= min(25.0, human_intervention_count * 4.0)
    return max(0.0, min(100.0, round(score, 1)))


def _map_arc_state_to_validation_trust(arc_state: str) -> str:
    if arc_state == "CONDITIONALLY_TRUSTED":
        return "CONDITIONALLY_TRUSTED"
    if arc_state == "TRUST_REVIEW_PENDING":
        return "TRUST_REVIEW_PENDING"
    if arc_state in {"UNPROVEN", "BLOCKED"}:
        return "UNPROVEN"
    return "PILOTING"


def _repo_pilot_progression(
    *,
    repository: str,
    sessions: tuple[str, ...],
) -> dict[str, Any]:
    audits = [_latest_audit(sid, repository=repository) for sid in sessions]
    p1 = _pilot_complete(audits[0] if len(audits) > 0 else None)
    p2 = _pilot2_alignment_demonstrated(audits[1] if len(audits) > 1 else None, sessions[1] if len(sessions) > 1 else "")
    p3 = _pilot_complete(audits[2] if len(audits) > 2 else None, require_pr_open=True)
    return {
        "progression_id": f"{repository}-pilot-progression",
        "pilot_1_complete": p1,
        "pilot_2_complete": p2,
        "pilot_3_complete": p3,
        "trust_review_ready": p3,
        "milestones": list(PILOT_VALIDATION_MILESTONES),
        "read_only": True,
    }


def _aethos_validation_row(*, session_id: str) -> dict[str, Any]:
    repository = PHASE_1_REPOSITORY
    sessions = REPOSITORY_PILOT_SESSIONS[repository]
    progression = _repo_pilot_progression(repository=repository, sessions=sessions)

    alignment = _alignment_score_for_sessions(sessions)
    interventions = _human_intervention_count(sessions)
    agent_metrics = _agent_metrics_for_session(sessions[-1]) if sessions else None
    agent_throughput = (agent_metrics or {}).get("throughput_score")

    p3_audit = _latest_audit(sessions[2], repository=repository) if len(sessions) > 2 else None
    pr_open = _pilot_complete(p3_audit, require_pr_open=True)
    pr_rate = 100.0 if pr_open else (0.0 if p3_audit else None)

    throughput = _derive_throughput_score(
        pilot_1_complete=progression["pilot_1_complete"],
        pilot_2_complete=progression["pilot_2_complete"],
        pilot_3_complete=progression["pilot_3_complete"],
        alignment_score=alignment,
        human_intervention_count=interventions,
        agent_throughput=float(agent_throughput) if agent_throughput is not None else None,
        pr_open_success=pr_open,
    )

    trust_state = (
        TRUST_RECOMMENDATION_FIX_186
        if progression["pilot_3_complete"]
        else "PILOTING"
    )

    return {
        "repository": repository,
        "display_name": REPOSITORY_DISPLAY_NAMES[repository],
        "trust_state": trust_state,
        "throughput_score": throughput,
        "alignment_score": alignment,
        "human_intervention_count": interventions,
        "pr_open_success_rate_percent": pr_rate,
        "agent_quality_metrics": agent_metrics,
        "pilot_progression": progression,
        "trust_progression": {
            "current_state": trust_state,
            "validation_states": list(VALIDATION_TRUST_STATES),
            "trust_granted_by_validation": False,
            "read_only": True,
        },
        "composes_fix_188": False,
        "composes_fix_189_190": agent_metrics is not None,
        "read_only": True,
    }


def _infer_pilotos_arc_state(*, progression: dict[str, Any], sessions: tuple[str, ...]) -> str:
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
        has_pilot_arc_trust_decision,
    )

    if has_pilot_arc_trust_decision():
        return "CONDITIONALLY_TRUSTED"
    if progression["pilot_3_complete"]:
        return "TRUST_REVIEW_PENDING"
    if progression["pilot_2_complete"]:
        return "PILOT_2_COMPLETE"
    if progression["pilot_1_complete"]:
        return "PILOT_1_COMPLETE"
    if any(_latest_audit(sid, repository=PILOTOS_UI_REPOSITORY) for sid in sessions):
        return "PILOTING"
    return "UNPROVEN"


def _pilotos_ui_validation_row(*, session_id: str) -> dict[str, Any]:
    repository = PILOTOS_UI_REPOSITORY
    sessions = REPOSITORY_PILOT_SESSIONS[repository]
    progression = _repo_pilot_progression(repository=repository, sessions=sessions)
    arc_state = _infer_pilotos_arc_state(progression=progression, sessions=sessions)
    sm_row = {
        "pilot_1_complete": progression["pilot_1_complete"],
        "pilot_2_complete": progression["pilot_2_complete"],
        "pilot_3_complete": progression["pilot_3_complete"],
    }

    alignment = _alignment_score_for_sessions(sessions)
    interventions = _human_intervention_count(sessions)
    agent_metrics = _agent_metrics_for_session(sessions[-1]) if sessions else None
    agent_throughput = (agent_metrics or {}).get("throughput_score")

    p3_audit = _latest_audit(sessions[2], repository=repository) if len(sessions) > 2 else None
    pr_open = bool(sm_row.get("pilot_3_complete")) or _pilot_complete(p3_audit, require_pr_open=True)
    pr_rate = 100.0 if pr_open else (0.0 if p3_audit else None)

    throughput = _derive_throughput_score(
        pilot_1_complete=bool(sm_row.get("pilot_1_complete") or progression["pilot_1_complete"]),
        pilot_2_complete=bool(sm_row.get("pilot_2_complete") or progression["pilot_2_complete"]),
        pilot_3_complete=bool(sm_row.get("pilot_3_complete") or progression["pilot_3_complete"]),
        alignment_score=alignment,
        human_intervention_count=interventions,
        agent_throughput=float(agent_throughput) if agent_throughput is not None else None,
        pr_open_success=pr_open,
    )

    return {
        "repository": repository,
        "display_name": REPOSITORY_DISPLAY_NAMES[repository],
        "trust_state": _map_arc_state_to_validation_trust(arc_state),
        "throughput_score": throughput,
        "alignment_score": alignment,
        "human_intervention_count": interventions,
        "pr_open_success_rate_percent": pr_rate,
        "agent_quality_metrics": agent_metrics,
        "pilot_progression": progression,
        "trust_progression": {
            "current_state": arc_state,
            "mapped_validation_state": _map_arc_state_to_validation_trust(arc_state),
            "trust_granted_by_validation": False,
            "read_only": True,
        },
        "composes_fix_188": True,
        "composes_fix_189_190": agent_metrics is not None,
        "read_only": True,
    }


def _infer_atlas_arc_state(*, progression: dict[str, Any], sessions: tuple[str, ...]) -> str:
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_store import (
        has_pilot_arc_trust_decision,
    )
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
        has_human_trust_decision_approve,
    )

    if has_pilot_arc_trust_decision() or (
        has_human_trust_decision_approve() and progression["pilot_3_complete"]
    ):
        return "CONDITIONALLY_TRUSTED"
    if progression["pilot_3_complete"]:
        return "TRUST_REVIEW_PENDING"
    if progression["pilot_2_complete"]:
        return "PILOT_2_COMPLETE"
    if progression["pilot_1_complete"]:
        return "PILOT_1_COMPLETE"
    if any(_latest_audit(sid, repository=ATLAS_TRADER_REPOSITORY) for sid in sessions):
        return "PILOTING"
    return "UNPROVEN"


def _atlas_trader_validation_row(*, session_id: str) -> dict[str, Any]:
    repository = ATLAS_TRADER_REPOSITORY
    sessions = REPOSITORY_PILOT_SESSIONS[repository]
    progression = _repo_pilot_progression(repository=repository, sessions=sessions)
    arc_state = _infer_atlas_arc_state(progression=progression, sessions=sessions)

    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
        has_atlas_trust_report_freeze_record,
        has_human_trust_decision_approve,
    )

    alignment = _alignment_score_for_sessions(sessions)
    interventions = _human_intervention_count(sessions)
    agent_metrics = _agent_metrics_for_session(sessions[-1]) if sessions else None
    agent_throughput = (agent_metrics or {}).get("throughput_score")

    p3_audit = _latest_audit(sessions[2], repository=repository) if len(sessions) > 2 else None
    pr_open = bool(progression.get("pilot_3_complete")) or _pilot_complete(p3_audit, require_pr_open=True)
    pr_rate = 100.0 if pr_open else (0.0 if p3_audit else None)

    throughput = _derive_throughput_score(
        pilot_1_complete=progression["pilot_1_complete"],
        pilot_2_complete=progression["pilot_2_complete"],
        pilot_3_complete=progression["pilot_3_complete"],
        alignment_score=alignment,
        human_intervention_count=interventions,
        agent_throughput=float(agent_throughput) if agent_throughput is not None else None,
        pr_open_success=pr_open,
    )

    evidence_complete = progression["pilot_3_complete"]
    trust_review_state = (
        "CONDITIONALLY_TRUSTED"
        if has_human_trust_decision_approve() and progression["pilot_3_complete"]
        else "TRUST_REVIEW_PENDING"
        if progression["pilot_3_complete"]
        else "PILOTING"
        if any(progression[k] for k in ("pilot_1_complete", "pilot_2_complete"))
        or any(_latest_audit(sid, repository=repository) for sid in sessions)
        else "UNPROVEN"
    )

    return {
        "repository": repository,
        "display_name": REPOSITORY_DISPLAY_NAMES[repository],
        "trust_state": _map_arc_state_to_validation_trust(arc_state),
        "throughput_score": throughput,
        "alignment_score": alignment,
        "human_intervention_count": interventions,
        "pr_open_success_rate_percent": pr_rate,
        "agent_quality_metrics": agent_metrics,
        "pilot_progression": progression,
        "evidence_completeness": "complete" if evidence_complete else "partial" if any(
            progression[k] for k in ("pilot_1_complete", "pilot_2_complete")
        ) else "none",
        "trust_review_state": trust_review_state,
        "trust_report_freeze_recorded": has_atlas_trust_report_freeze_record(),
        "human_trust_decision_approve": has_human_trust_decision_approve(),
        "trust_progression": {
            "current_state": arc_state,
            "mapped_validation_state": _map_arc_state_to_validation_trust(arc_state),
            "trust_granted_by_validation": False,
            "read_only": True,
        },
        "composes_fix_193": True,
        "composes_fix_194_trust_freeze": has_atlas_trust_report_freeze_record(),
        "composes_fix_189_190": agent_metrics is not None,
        "read_only": True,
    }


def _infer_nexora_arc_state(*, progression: dict[str, Any], sessions: tuple[str, ...]) -> str:
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
        has_pilot_arc_trust_decision,
    )
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
        has_human_trust_decision_approve,
    )

    if has_pilot_arc_trust_decision() or (
        has_human_trust_decision_approve() and progression["pilot_3_complete"]
    ):
        return "CONDITIONALLY_TRUSTED"
    if progression["pilot_3_complete"]:
        return "TRUST_REVIEW_PENDING"
    if progression["pilot_2_complete"]:
        return "PILOT_2_COMPLETE"
    if progression["pilot_1_complete"]:
        return "PILOT_1_COMPLETE"
    if any(_latest_audit(sid, repository=NEXORA_REPOSITORY) for sid in sessions):
        return "PILOTING"
    return "UNPROVEN"


def _nexora_validation_row(*, session_id: str) -> dict[str, Any]:
    repository = NEXORA_REPOSITORY
    sessions = REPOSITORY_PILOT_SESSIONS[repository]
    progression = _repo_pilot_progression(repository=repository, sessions=sessions)
    arc_state = _infer_nexora_arc_state(progression=progression, sessions=sessions)

    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
        has_human_trust_decision_approve,
        has_nexora_trust_report_freeze_record,
    )

    alignment = _alignment_score_for_sessions(sessions)
    interventions = _human_intervention_count(sessions)
    agent_metrics = _agent_metrics_for_session(sessions[-1]) if sessions else None
    agent_throughput = (agent_metrics or {}).get("throughput_score")

    p3_audit = _latest_audit(sessions[2], repository=repository) if len(sessions) > 2 else None
    pr_open = bool(progression.get("pilot_3_complete")) or _pilot_complete(p3_audit, require_pr_open=True)
    pr_rate = 100.0 if pr_open else (0.0 if p3_audit else None)

    throughput = _derive_throughput_score(
        pilot_1_complete=progression["pilot_1_complete"],
        pilot_2_complete=progression["pilot_2_complete"],
        pilot_3_complete=progression["pilot_3_complete"],
        alignment_score=alignment,
        human_intervention_count=interventions,
        agent_throughput=float(agent_throughput) if agent_throughput is not None else None,
        pr_open_success=pr_open,
    )

    evidence_complete = progression["pilot_3_complete"]
    trust_review_state = (
        "CONDITIONALLY_TRUSTED"
        if has_human_trust_decision_approve() and progression["pilot_3_complete"]
        else "TRUST_REVIEW_PENDING"
        if progression["pilot_3_complete"]
        else "PILOTING"
        if any(progression[k] for k in ("pilot_1_complete", "pilot_2_complete"))
        or any(_latest_audit(sid, repository=repository) for sid in sessions)
        else "UNPROVEN"
    )

    return {
        "repository": repository,
        "display_name": REPOSITORY_DISPLAY_NAMES[repository],
        "trust_state": _map_arc_state_to_validation_trust(arc_state),
        "throughput_score": throughput,
        "alignment_score": alignment,
        "human_intervention_count": interventions,
        "pr_open_success_rate_percent": pr_rate,
        "agent_quality_metrics": agent_metrics,
        "pilot_progression": progression,
        "evidence_completeness": "complete" if evidence_complete else "partial" if any(
            progression[k] for k in ("pilot_1_complete", "pilot_2_complete")
        ) else "none",
        "trust_review_state": trust_review_state,
        "trust_report_freeze_recorded": has_nexora_trust_report_freeze_record(),
        "human_trust_decision_approve": has_human_trust_decision_approve(),
        "trust_progression": {
            "current_state": arc_state,
            "mapped_validation_state": _map_arc_state_to_validation_trust(arc_state),
            "trust_granted_by_validation": False,
            "read_only": True,
        },
        "composes_fix_195": True,
        "composes_fix_196_trust_freeze": has_nexora_trust_report_freeze_record(),
        "composes_fix_189_190": agent_metrics is not None,
        "read_only": True,
    }


def _unproven_validation_row(*, repository: str) -> dict[str, Any]:
    return {
        "repository": repository,
        "display_name": REPOSITORY_DISPLAY_NAMES.get(repository, repository),
        "trust_state": "UNPROVEN",
        "throughput_score": None,
        "alignment_score": None,
        "human_intervention_count": 0,
        "pr_open_success_rate_percent": None,
        "agent_quality_metrics": None,
        "pilot_progression": {
            "progression_id": f"{repository}-pilot-progression",
            "pilot_1_complete": False,
            "pilot_2_complete": False,
            "pilot_3_complete": False,
            "trust_review_ready": False,
            "milestones": list(PILOT_VALIDATION_MILESTONES),
            "read_only": True,
        },
        "trust_progression": {
            "current_state": "UNPROVEN",
            "validation_states": list(VALIDATION_TRUST_STATES),
            "trust_granted_by_validation": False,
            "read_only": True,
        },
        "composes_fix_188": False,
        "composes_fix_189_190": False,
        "read_only": True,
    }


def _cross_repo_evidence_registry(*, validation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for row in validation_rows:
        repository = str(row.get("repository") or "")
        sessions = REPOSITORY_PILOT_SESSIONS.get(repository, ())
        for idx, session_id in enumerate(sessions, start=1):
            audit = _latest_audit(session_id, repository=repository)
            if audit:
                entries.append(
                    {
                        "evidence_id": f"{repository}-pilot-{idx}-audit",
                        "repository": repository,
                        "kind": "pilot_audit",
                        "session_id": session_id,
                        "audit_id": audit.get("audit_id"),
                        "pilot_outcome": audit.get("outcome"),
                        "repo_issue": audit.get("repo_issue"),
                        "read_only": True,
                    }
                )
        if repository == PHASE_1_REPOSITORY:
            receipt_dir = _repo_root() / "data" / "dogfood_pilot_3_receipts"
            if receipt_dir.is_dir():
                for path in sorted(receipt_dir.glob("*.json"))[-2:]:
                    entries.append(
                        {
                            "evidence_id": f"{repository}-receipt-{path.stem}",
                            "repository": repository,
                            "kind": "live_receipt",
                            "receipt_path": str(path.relative_to(_repo_root())),
                            "read_only": True,
                        }
                    )
        if repository == PILOTOS_UI_REPOSITORY:
            from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
                list_pilotos_ui_pilot_arc_orchestrator_records,
            )

            for record in list_pilotos_ui_pilot_arc_orchestrator_records()[-5:]:
                if str(record.get("kind") or "") == "pilot_arc_trust_decision":
                    entries.append(
                        {
                            "evidence_id": f"{repository}-trust-{record.get('record_id')}",
                            "repository": repository,
                            "kind": "trust_decision",
                            "record_id": record.get("record_id"),
                            "content": record.get("content"),
                            "read_only": True,
                        }
                    )
        if repository == ATLAS_TRADER_REPOSITORY:
            from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
                list_atlas_trader_trust_report_freeze_records,
            )

            for record in list_atlas_trader_trust_report_freeze_records()[-5:]:
                kind = str(record.get("kind") or "")
                if kind.startswith("human_trust_decision_") or kind == "atlas_trust_report_freeze_artifact":
                    entries.append(
                        {
                            "evidence_id": f"{repository}-trust-freeze-{record.get('record_id')}",
                            "repository": repository,
                            "kind": kind,
                            "record_id": record.get("record_id"),
                            "content": record.get("content"),
                            "read_only": True,
                        }
                    )
        if repository == NEXORA_REPOSITORY:
            from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
                list_nexora_pilot_arc_orchestrator_records,
            )
            from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
                list_nexora_trust_report_freeze_records,
            )

            for record in list_nexora_pilot_arc_orchestrator_records()[-5:]:
                if str(record.get("kind") or "") in {
                    "pilot_arc_trust_decision",
                    "nexora_pilot_observation",
                    "nexora_pilot_intervention",
                }:
                    entries.append(
                        {
                            "evidence_id": f"{repository}-arc-{record.get('record_id')}",
                            "repository": repository,
                            "kind": str(record.get("kind") or ""),
                            "record_id": record.get("record_id"),
                            "content": record.get("content"),
                            "read_only": True,
                        }
                    )
            for record in list_nexora_trust_report_freeze_records()[-5:]:
                kind = str(record.get("kind") or "")
                if kind.startswith("human_trust_decision_") or kind == "nexora_trust_report_freeze_artifact":
                    entries.append(
                        {
                            "evidence_id": f"{repository}-trust-freeze-{record.get('record_id')}",
                            "repository": repository,
                            "kind": kind,
                            "record_id": record.get("record_id"),
                            "content": record.get("content"),
                            "read_only": True,
                        }
                    )
    return entries


def _delivery_generalization_assessment(*, validation_rows: list[dict[str, Any]]) -> dict[str, Any]:
    proven = [r for r in validation_rows if r.get("trust_state") == "CONDITIONALLY_TRUSTED"]
    piloting = [r for r in validation_rows if r.get("trust_state") == "PILOTING"]
    unproven = [r for r in validation_rows if r.get("trust_state") == "UNPROVEN"]
    return {
        "assessment_id": "delivery-generalization",
        "aethos_proven": any(r.get("repository") == PHASE_1_REPOSITORY for r in proven),
        "cross_repo_piloting_count": len(piloting),
        "unproven_count": len(unproven),
        "merge_deploy_premature": len(proven) < 2,
        "largest_unknown": "Does AethOS delivery generalize across repositories?",
        "validation_grants_trust": False,
        "read_only": True,
    }


def build_cross_repository_multi_agent_delivery_validation(
    *, session_id: str
) -> CrossRepositoryMultiAgentDeliveryValidationResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_cross_repository_multi_agent_delivery_validation_records(session_id=sid)

    validation_rows: list[dict[str, Any]] = [
        _aethos_validation_row(session_id=sid),
        _pilotos_ui_validation_row(session_id=sid),
        _atlas_trader_validation_row(session_id=sid),
        _nexora_validation_row(session_id=sid),
    ]

    sections = {
        "cross_repository_validation_matrix": validation_rows,
        "cross_repo_evidence_registry": _cross_repo_evidence_registry(validation_rows=validation_rows),
        "delivery_generalization_assessment": [_delivery_generalization_assessment(validation_rows=validation_rows)],
        "forbidden_validation_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_VALIDATION_ACTIONS
        ],
        "operator_validation_records": [{**r, "read_only": True} for r in records],
    }

    payload: dict[str, Any] = {
        "schema_version": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_SCHEMA_VERSION,
        "fix": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_191,
        "execution_performed": EXECUTION_PERFORMED_FIX_191,
        "pilot_reexecution_performed": False,
        "validation_compose_artifacts_only": VALIDATION_COMPOSES_ARTIFACTS_ONLY_FIX_191,
        "cross_repo_validation_grants_trust": CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
        "trust_transfer_enabled": TRUST_TRANSFER_ENABLED_FIX_191,
        "merge_authority": MERGE_AUTHORITY_FIX_191,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_191,
        "railway_authority": RAILWAY_AUTHORITY_FIX_191,
        "provider_authority": PROVIDER_AUTHORITY_FIX_191,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_191,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_191,
        "invariant": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_INVARIANT,
        "session_id": sid,
        "repositories": list(VALIDATION_REPOSITORIES),
        "sections": sections,
        "validation_record_count": len(records),
        "fix_191_certification_requirements": list(FIX_191_CERTIFICATION_REQUIREMENTS),
        "cross_repository_multi_agent_delivery_validation_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_PRINCIPLES
        ],
        "sources": {
            "composes_fix_188_pilot_arc": True,
            "composes_fix_193_atlas_pilot_arc": True,
            "composes_fix_194_atlas_trust_freeze": True,
            "composes_fix_195_nexora_pilot_arc": True,
            "composes_fix_189_agent_execution": True,
            "composes_fix_190_metrics": True,
            "pilot_rerun_performed": False,
        },
    }

    return CrossRepositoryMultiAgentDeliveryValidationResult(
        ok=True,
        session_id=sid,
        cross_repository_multi_agent_delivery_validation=payload,
        detail="Cross-repository multi-agent delivery validation assembled (validation ≠ trust granting).",
    )
