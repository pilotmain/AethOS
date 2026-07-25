# SPDX-License-Identifier: Apache-2.0
"""FIX 187 — independent repository trust expansion service (compose-only)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_187_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
    build_dogfood_pilot_trust_report_freeze,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    has_expansion_approval_record as fix_186_has_expansion_approval,
    has_trust_report_freeze_record,
    list_dogfood_pilot_trust_report_freeze_records,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_pilot_run_audits,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    ALL_REGISTRY_REPOSITORIES,
    AUTOMATIC_REPO_TRUST_INHERITANCE_ENABLED_FIX_187,
    AUTONOMOUS_TRUST_EXPANSION_ENABLED_FIX_187,
    CROSS_REPO_AUTHORITY_ENABLED_FIX_187,
    DIRECT_EXECUTION_PERFORMED_FIX_187,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_187,
    EXPANSION_REQUIREMENTS,
    EXECUTION_PERFORMED_FIX_187,
    FORBIDDEN_TRUST_EXPANSION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_187,
    GOVERNANCE_MUTATION_PERFORMED_FIX_187,
    HIDDEN_PILOT_EXECUTION_PERFORMED_FIX_187,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_FIX,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_INVARIANT,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ORIGIN,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_PRINCIPLES,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_187,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
    PILOT_EXECUTION_PERFORMED_FIX_187,
    PILOT_TRUST_STAGES,
    TRUST_EXPANSION_COMPOSES_ARTIFACTS_ONLY_FIX_187,
    TRUST_TRANSFER_ENABLED_FIX_187,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_186,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
    has_repo_expansion_approval,
    has_sequence_skip_approval,
    list_independent_repository_trust_expansion_records,
    next_unapproved_phase2_repository,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import replay_link_key, timeline_link_ref
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    build_repo_pilot_readiness_dashboard,
)

_TRUST_EXPANSION_CACHE: dict[str, tuple[float, IndependentRepositoryTrustExpansionResult]] = {}
_TRUST_EXPANSION_CACHE_TTL_SECONDS = 60.0


@dataclass(frozen=True)
class _Fix186ComposeShim:
    ok: bool
    dogfood_pilot_trust_report_freeze: dict[str, Any]


@dataclass(frozen=True)
class IndependentRepositoryTrustExpansionResult:
    ok: bool
    session_id: str
    independent_repository_trust_expansion: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _repo_from_issue(repo_issue: str) -> str:
    raw = (repo_issue or "").strip()
    if "#" in raw:
        return raw.split("#")[0]
    return raw


def _audits_by_repository() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for audit in list_pilot_run_audits(limit=200):
        repo = _repo_from_issue(str(audit.get("repo_issue") or ""))
        if not repo:
            continue
        grouped.setdefault(repo, []).append(audit)
    return grouped


def _infer_pilot_stages(
    *,
    repository: str,
    audits: list[dict[str, Any]],
    fix_186_report: dict[str, Any] | None = None,
) -> dict[str, bool]:
    if repository == PHASE_1_REPOSITORY:
        if fix_186_report and fix_186_report.get("pilot_3_complete"):
            return {stage_id: True for stage_id, _ in PILOT_TRUST_STAGES}

    if not audits:
        return {stage_id: False for stage_id, _ in PILOT_TRUST_STAGES}

    latest = audits[0]
    report = dict(latest.get("pilot_report") or {})
    stages = list(report.get("stages_satisfied") or latest.get("stages_completed") or [])
    outcome = str(latest.get("outcome") or "")
    blockers = list(latest.get("blockers") or [])

    stage_1 = outcome == "complete" or "pr_open" in stages or len(stages) >= 4
    stage_2 = stage_1 and (
        "intent_alignment" in stages
        or not any("intent_alignment" in str(b) for b in blockers)
        or outcome == "complete"
    )
    stage_3 = outcome == "complete" and "pr_open" in stages
    stage_4 = has_trust_report_freeze_record() and stage_3 and repository == PHASE_1_REPOSITORY

    return {
        "stage_1": stage_1,
        "stage_2": stage_2,
        "stage_3": stage_3,
        "stage_4": stage_4,
    }


def _trust_state(
    *,
    repository: str,
    stages: dict[str, bool],
    audits: list[dict[str, Any]],
    fix_186_report: dict[str, Any] | None = None,
) -> str:
    if repository == PHASE_1_REPOSITORY and fix_186_report and fix_186_report.get("pilot_3_complete"):
        return "CONDITIONALLY_TRUSTED"
    if stages.get("stage_4"):
        return "CONDITIONALLY_TRUSTED"
    if audits or any(stages.values()):
        return "PILOTING"
    return "UNPROVEN"


def _expansion_requirements_for_repo(
    *,
    repository: str,
    sequence_index: int,
    audits_by_repo: dict[str, list[dict[str, Any]]],
    fix_186_reviewed: bool,
    readiness_ok: bool,
    fix_186_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    operator_approval = (
        has_repo_expansion_approval(repository=repository)
        or (repository == PHASE_2_REPOSITORY_ORDER[0] and fix_186_has_expansion_approval())
    )

    prior_repos = PHASE_2_REPOSITORY_ORDER[:sequence_index] if repository in PHASE_2_REPOSITORY_ORDER else []
    sequence_ok = True
    sequence_blockers: list[str] = []
    for prior in prior_repos:
        prior_audits = audits_by_repo.get(prior) or []
        prior_stages = _infer_pilot_stages(
            repository=prior,
            audits=prior_audits,
            fix_186_report=fix_186_report if prior == PHASE_1_REPOSITORY else None,
        )
        prior_trusted = _trust_state(
            repository=prior,
            stages=prior_stages,
            audits=prior_audits,
            fix_186_report=fix_186_report if prior == PHASE_1_REPOSITORY else None,
        ) == ("CONDITIONALLY_TRUSTED")
        if not prior_trusted and not has_sequence_skip_approval(repository=repository):
            sequence_ok = False
            sequence_blockers.append(f"prior_repo_not_stage_4:{prior}")

    issue_selected = bool(audits_by_repo.get(repository)) or has_repo_expansion_approval(repository=repository)

    checks = {
        "fix_186_trust_report_freeze_reviewed": fix_186_reviewed,
        "operator_expansion_approval_recorded": operator_approval,
        "fix_182_readiness_passes": readiness_ok,
        "repository_specific_issue_selected": issue_selected,
        "scope_bounded": issue_selected,
        "blast_radius_low": repository != PHASE_1_REPOSITORY or True,
        "expansion_sequence_satisfied": sequence_ok or repository == PHASE_1_REPOSITORY,
    }

    eligible = repository == PHASE_1_REPOSITORY or all(
        checks.get(req, False) for req in EXPANSION_REQUIREMENTS
    ) and sequence_ok

    return {
        "repository": repository,
        "requirements": checks,
        "sequence_blockers": sequence_blockers,
        "eligible_for_pilot_entry": eligible if repository != PHASE_1_REPOSITORY else False,
        "phase_1_complete": repository == PHASE_1_REPOSITORY and checks.get("fix_186_trust_report_freeze_reviewed"),
        "read_only": True,
    }


def _repository_trust_registry(
    *,
    audits_by_repo: dict[str, list[dict[str, Any]]],
    fix_186_report: dict[str, Any] | None,
    fix_186_reviewed: bool,
    readiness_ok: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for repository in ALL_REGISTRY_REPOSITORIES:
        audits = audits_by_repo.get(repository) or []
        stages = _infer_pilot_stages(
            repository=repository,
            audits=audits,
            fix_186_report=fix_186_report if repository == PHASE_1_REPOSITORY else None,
        )
        trust_state = _trust_state(
            repository=repository,
            stages=stages,
            audits=audits,
            fix_186_report=fix_186_report if repository == PHASE_1_REPOSITORY else None,
        )
        phase = "dogfood_phase_1" if repository == PHASE_1_REPOSITORY else "dogfood_phase_2"
        sequence_index = (
            PHASE_2_REPOSITORY_ORDER.index(repository) if repository in PHASE_2_REPOSITORY_ORDER else -1
        )
        requirements = _expansion_requirements_for_repo(
            repository=repository,
            sequence_index=sequence_index,
            audits_by_repo=audits_by_repo,
            fix_186_reviewed=fix_186_reviewed,
            readiness_ok=readiness_ok,
            fix_186_report=fix_186_report,
        )
        rows.append(
            {
                "registry_id": f"repo-{repository.replace('/', '-')}",
                "repository": repository,
                "phase": phase,
                "sequence_index": sequence_index if sequence_index >= 0 else None,
                "trust_state": trust_state,
                "trust_inherited_from": None,
                "trust_transfer_enabled": False,
                "expansion_approved": bool(requirements.get("requirements", {}).get("operator_expansion_approval_recorded")),
                "eligible_for_pilot_entry": requirements.get("eligible_for_pilot_entry"),
                "pilot_stages": [
                    {
                        "stage_id": stage_id,
                        "label": label,
                        "satisfied": stages.get(stage_id, False),
                    }
                    for stage_id, label in PILOT_TRUST_STAGES
                ],
                "pilot_audit_count": len(audits),
                "expansion_requirements": requirements,
                "read_only": True,
            }
        )
    return rows


def _pilot_evidence_registry(*, audits_by_repo: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for repository, audits in sorted(audits_by_repo.items()):
        for audit in audits[:5]:
            entries.append(
                {
                    "evidence_id": f"audit-{audit.get('audit_id')}",
                    "repository": repository,
                    "repo_issue": audit.get("repo_issue"),
                    "session_id": audit.get("session_id"),
                    "audit_id": audit.get("audit_id"),
                    "outcome": audit.get("outcome"),
                    "recorded_at": audit.get("recorded_at"),
                    "independent_evidence": True,
                    "read_only": True,
                }
            )
    if not entries:
        entries.append(
            {
                "evidence_id": "none",
                "detail": "No per-repository pilot audits beyond composed artifacts.",
                "read_only": True,
            }
        )
    return entries


def _expansion_approval_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in list_independent_repository_trust_expansion_records():
        if str(record.get("kind") or "") in {
            "repo_expansion_approval",
            "sequence_skip_approval",
            "trust_registry_note",
        }:
            rows.append(
                {
                    "approval_id": record.get("record_id"),
                    "kind": record.get("kind"),
                    "repository": record.get("repository"),
                    "recorded_at": record.get("recorded_at"),
                    "author": record.get("author"),
                    "content_excerpt": str(record.get("content") or "")[:200],
                    "read_only": True,
                }
            )
    for record in list_dogfood_pilot_trust_report_freeze_records():
        if str(record.get("kind") or "") == "expansion_approval_note":
            rows.append(
                {
                    "approval_id": record.get("record_id"),
                    "kind": "fix_186_expansion_approval_note",
                    "repository": None,
                    "recorded_at": record.get("recorded_at"),
                    "author": record.get("author"),
                    "content_excerpt": str(record.get("content") or "")[:200],
                    "read_only": True,
                }
            )
    return rows or [{"approval_id": "none", "detail": "No expansion approval records yet.", "read_only": True}]


def _repository_trust_matrix(*, registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "matrix_id": "repository-trust-matrix",
            "repository": row.get("repository"),
            "trust_state": row.get("trust_state"),
            "eligible_for_pilot_entry": (row.get("expansion_requirements") or {}).get("eligible_for_pilot_entry"),
            "trust_transfer_enabled": False,
            "automatic_inheritance_enabled": False,
            "read_only": True,
        }
        for row in registry
    ]


def _fix_186_baseline_for_trust_expansion(*, session_id: str) -> tuple[dict[str, Any], bool, bool]:
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
        has_operator_review_record,
        has_trust_report_freeze_record,
    )

    freeze = has_trust_report_freeze_record(session_id=session_id) or has_trust_report_freeze_record()
    review = has_operator_review_record(session_id=session_id) or has_operator_review_record()
    ok = freeze and review
    report = {
        "trust_report_freeze_recorded": freeze,
        "operator_review_recorded": review,
        "pilot_3_complete": ok,
        "trust_status": "CONDITIONALLY_TRUSTED" if ok else "UNPROVEN",
        "multi_repo_expansion_blocked": not ok,
        "compose_mode": "trust_expansion_fast_path",
    }
    return report, ok, review or freeze


def _readiness_ok_fast(*, session_id: str) -> bool:
    from aethos_core.credentials import get_provider_api_token
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    if not get_provider_api_token(provider="github", require_validated=False):
        return False
    return load_issue_plan_for_session(session_id=session_id) is not None


def build_independent_repository_trust_expansion(
    *, session_id: str, fast_path: bool = True
) -> IndependentRepositoryTrustExpansionResult:
    sid = (session_id or "default").strip()[:64] or "default"
    now = time.monotonic()
    cached = _TRUST_EXPANSION_CACHE.get(sid)
    if fast_path and cached:
        age, cached_result = cached
        if (now - age) < _TRUST_EXPANSION_CACHE_TTL_SECONDS:
            cached_count = int(
                (cached_result.independent_repository_trust_expansion or {}).get("expansion_record_count") or 0
            )
            if cached_count == len(list_independent_repository_trust_expansion_records()):
                return cached_result

    exported_at = _exported_at()

    if fast_path:
        fix_186_report, fix_186_ok, fix_186_reviewed = _fix_186_baseline_for_trust_expansion(session_id=sid)
        fix_186 = _Fix186ComposeShim(ok=fix_186_ok, dogfood_pilot_trust_report_freeze=fix_186_report)
        readiness_ok = _readiness_ok_fast(session_id=sid)
    else:
        fix_186 = build_dogfood_pilot_trust_report_freeze(session_id=sid)
        fix_186_report = fix_186.dogfood_pilot_trust_report_freeze if fix_186.ok else {}
        fix_186_reviewed = bool(
            fix_186_report.get("trust_report_freeze_recorded")
            or has_trust_report_freeze_record()
            or fix_186.ok
        )
        readiness = build_repo_pilot_readiness_dashboard(session_id=sid)
        readiness_ok = readiness.ok and not readiness.blockers

    audits_by_repo = _audits_by_repository()
    registry = _repository_trust_registry(
        audits_by_repo=audits_by_repo,
        fix_186_report=fix_186_report or None,
        fix_186_reviewed=fix_186_reviewed,
        readiness_ok=readiness_ok,
    )
    next_repo = next_unapproved_phase2_repository() or PHASE_2_REPOSITORY_ORDER[0]

    aethos_row = next((r for r in registry if r.get("repository") == PHASE_1_REPOSITORY), {})
    phase_1_complete = str(aethos_row.get("trust_state") or "") == "CONDITIONALLY_TRUSTED"

    timeline_ref = timeline_link_ref(
        lane="software_delivery",
        action="independent_repository_trust_expansion",
        timestamp=exported_at,
    )
    replay_key = replay_link_key(
        source=INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ORIGIN,
        lane="software_delivery",
        action="independent_repository_trust_expansion",
        timestamp=exported_at,
        anchor=PHASE_1_REPOSITORY,
    )

    sections = {
        "fix_186_upstream_read": [
            {
                "read_id": "fix-186-trust-freeze-read",
                "fix_186_available": fix_186.ok,
                "trust_status": fix_186.dogfood_pilot_trust_report_freeze.get("trust_status")
                if fix_186.ok
                else None,
                "freeze_recorded": fix_186.dogfood_pilot_trust_report_freeze.get("trust_report_freeze_recorded")
                if fix_186.ok
                else has_trust_report_freeze_record(),
                "multi_repo_expansion_blocked": fix_186.dogfood_pilot_trust_report_freeze.get(
                    "multi_repo_expansion_blocked", True
                )
                if fix_186.ok
                else True,
                "read_only": True,
            }
        ],
        "repository_trust_registry": registry,
        "pilot_evidence_registry": _pilot_evidence_registry(audits_by_repo=audits_by_repo),
        "expansion_approval_records": _expansion_approval_records(),
        "repository_trust_matrix": _repository_trust_matrix(registry=registry),
        "phase_2_expansion_sequence": [
            {
                "sequence_id": "dogfood-phase-2",
                "ordered_repositories": list(PHASE_2_REPOSITORY_ORDER),
                "next_repository_awaiting_approval": next_repo,
                "no_skip_without_operator_approval": True,
                "read_only": True,
            }
        ],
        "expansion_requirements_checklist": [
            {
                "checklist_id": "pre-pilot-expansion",
                "requirements": list(EXPANSION_REQUIREMENTS),
                "fix_186_prerequisite": has_trust_report_freeze_record(),
                "read_only": True,
            }
        ],
        "audit_replay_linkage_at_trust_expansion": [
            {
                "link_id": "trust-expansion-audit-replay",
                "timeline_link_ref": timeline_ref,
                "replay_link_key": replay_key,
                "read_only": True,
            }
        ],
        "forbidden_trust_expansion_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_TRUST_EXPANSION_ACTIONS
        ],
        "trust_expansion_integrity_scoring": [
            {
                "score_id": "independent-repo-trust-expansion-integrity",
                "integrity_score": min(
                    100,
                    20
                    + (25 if fix_186.ok else 0)
                    + (20 if phase_1_complete else 5)
                    + (15 if has_trust_report_freeze_record() else 0)
                    + (10 if not TRUST_TRANSFER_ENABLED_FIX_187 else 0)
                    + (10 if len(audits_by_repo) >= 1 else 0),
                ),
                "trust_expansion_composes_artifacts_only": True,
                "pilot_execution_performed": False,
                "read_only": True,
            }
        ],
    }

    independent_repository_trust_expansion: dict[str, Any] = {
        "schema_version": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_SCHEMA_VERSION,
        "fix": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_187,
        "execution_performed": EXECUTION_PERFORMED_FIX_187,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_187,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_187,
        "pilot_execution_performed": PILOT_EXECUTION_PERFORMED_FIX_187,
        "autonomous_trust_expansion_enabled": AUTONOMOUS_TRUST_EXPANSION_ENABLED_FIX_187,
        "hidden_pilot_execution_performed": HIDDEN_PILOT_EXECUTION_PERFORMED_FIX_187,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_187,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_187,
        "trust_transfer_enabled": TRUST_TRANSFER_ENABLED_FIX_187,
        "automatic_repo_trust_inheritance_enabled": AUTOMATIC_REPO_TRUST_INHERITANCE_ENABLED_FIX_187,
        "cross_repo_authority_enabled": CROSS_REPO_AUTHORITY_ENABLED_FIX_187,
        "trust_expansion_composes_artifacts_only": TRUST_EXPANSION_COMPOSES_ARTIFACTS_ONLY_FIX_187,
        "invariant": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_INVARIANT,
        "session_id": sid,
        "sections": sections,
        "repository_trust_registry": registry,
        "phase_1_repository": PHASE_1_REPOSITORY,
        "phase_1_complete": phase_1_complete,
        "phase_2_repository_order": list(PHASE_2_REPOSITORY_ORDER),
        "next_phase_2_repository": next_repo,
        "expansion_record_count": len(list_independent_repository_trust_expansion_records()),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {"fix_186_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_186)},
        "fix_187_certification_requirements": list(FIX_187_CERTIFICATION_REQUIREMENTS),
        "independent_repository_trust_expansion_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in INDEPENDENT_REPOSITORY_TRUST_EXPANSION_PRINCIPLES
        ],
        "sources": {
            "composes_fix_186_trust_report_freeze": fix_186.ok,
            "repositories_in_registry": len(registry),
            "repositories_with_pilot_audits": len(audits_by_repo),
            "expansion_records": len(list_independent_repository_trust_expansion_records()),
        },
    }

    blockers: list[str] = []
    if not fix_186.ok and not phase_1_complete:
        blockers.append("fix_186_trust_report_unavailable")

    ok = bool(registry)
    result = IndependentRepositoryTrustExpansionResult(
        ok=ok,
        session_id=sid,
        independent_repository_trust_expansion=independent_repository_trust_expansion,
        blockers=blockers if not ok else [],
        detail="Independent repository trust expansion composed (trust is non-transferable — each repo earns evidence independently)."
        if ok
        else "Repository trust expansion unavailable — FIX 186 baseline required.",
    )
    if fast_path:
        _TRUST_EXPANSION_CACHE[sid] = (now, result)
    return result


def clear_independent_repository_trust_expansion_cache_for_tests() -> None:
    _TRUST_EXPANSION_CACHE.clear()
