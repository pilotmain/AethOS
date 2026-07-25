# SPDX-License-Identifier: Apache-2.0
"""FIX 182 — repo pilot readiness dashboard (composes FIX 181)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.governance.governance_friction_approval_contract import FIX_182_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
    PILOT_DEFAULT_REPO,
    PILOT_DEFAULT_REPO_ISSUE,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
    build_end_to_end_repo_development_pilot_harness,
)
from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.job_replay.job_replay_deep_link import (
    replay_link_key,
    timeline_link_ref,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_contract import (
    AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182,
    DIRECT_EXECUTION_PERFORMED_FIX_182,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182,
    EXECUTION_PERFORMED_FIX_182,
    FORBIDDEN_READINESS_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_182,
    GOVERNANCE_MUTATION_PERFORMED_FIX_182,
    HIDDEN_PILOT_EXECUTION_PERFORMED_FIX_182,
    MUTATION_PERFORMED_FIX_182,
    PILOT_EXECUTION_PERFORMED_FIX_182,
    READINESS_VISIBILITY_ONLY_FIX_182,
    REPO_PILOT_READINESS_DASHBOARD_FIX,
    REPO_PILOT_READINESS_DASHBOARD_INVARIANT,
    REPO_PILOT_READINESS_DASHBOARD_ORIGIN,
    REPO_PILOT_READINESS_DASHBOARD_PRINCIPLES,
    REPO_PILOT_READINESS_DASHBOARD_SCHEMA_VERSION,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_store import (
    list_repo_pilot_readiness_dashboard_records,
)
from aethos_core.provider_topology.github_access_verifier import verify_github_repo_access
from aethos_core.software_delivery.github_pr_open_contract import GITHUB_PR_OPEN_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_preflight_contract import GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE
from aethos_core.software_delivery.pr_draft_contract import GITHUB_PR_CREATION_ENABLED_FIX_125F
from aethos_core.software_delivery.software_delivery_phase_2_contract import (
    SOFTWARE_DELIVERY_APPROVAL_PHRASES,
    SOFTWARE_DELIVERY_DEPLOY_ENABLED,
    SOFTWARE_DELIVERY_MERGE_ENABLED,
    SOFTWARE_DELIVERY_PHASE_2_FROZEN,
    SOFTWARE_DELIVERY_RAILWAY_MUTATION_ENABLED,
)

_REPO_ISSUE_RX = re.compile(r"^[\w.-]+/[\w.-]+#\d+$", re.I)


@dataclass(frozen=True)
class RepoPilotReadinessDashboardResult:
    ok: bool
    session_id: str
    repo_pilot_readiness_dashboard: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _resolve_repo_issue(*, records: list[dict[str, Any]], harness: dict[str, Any]) -> tuple[str, str]:
    repo_issue = str(harness.get("repo_issue") or PILOT_DEFAULT_REPO_ISSUE).strip()
    for kind in ("repo_selection_note", "issue_selection_note", "readiness_artifact"):
        rows = _by_kind(records, kind)
        if rows:
            content = str(rows[-1].get("content") or "").strip()
            if "#" in content:
                return content, content.split("#")[0]
            if "/" in content:
                issue = repo_issue.split("#")[-1] if "#" in repo_issue else "80"
                return f"{content}#{issue}", content
    if "#" in repo_issue:
        return repo_issue, repo_issue.split("#")[0]
    return PILOT_DEFAULT_REPO_ISSUE, PILOT_DEFAULT_REPO


def _pilot_harness_upstream_read(*, harness: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "read_id": "fix-181-pilot-harness-read",
            "upstream_fix": "FIX 181",
            "pilot_ready": harness.get("pilot_ready"),
            "repo_issue": harness.get("repo_issue"),
            "pending_command_count": harness.get("pending_command_count"),
            "pilot_harness_not_autonomous_execution": harness.get("pilot_harness_not_autonomous_execution"),
            "read_only": True,
            "recomputed_by_fix_182": False,
        }
    ]


def _repo_selection_readiness(*, repo: str) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    access = verify_github_repo_access(repo)
    ready = access.ok and "/" in repo
    if not ready:
        blockers.append("repo_not_accessible" if repo else "repo_not_selected")
    return [
        {
            "selection_id": "repo-selection",
            "repo": repo,
            "github_access_verified": access.ok,
            "access_message": access.message,
            "ready": ready,
            "read_only": True,
        }
    ], blockers


def _issue_selection_readiness(*, repo_issue: str) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    valid_format = bool(_REPO_ISSUE_RX.match(repo_issue.strip()))
    if not valid_format:
        blockers.append("issue_format_invalid")
    cert_mode = os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}
    issue_ready = valid_format and (cert_mode or repo_issue.strip())
    return [
        {
            "selection_id": "issue-selection",
            "repo_issue": repo_issue,
            "format_valid": valid_format,
            "issue_ready": issue_ready,
            "certification_mode": cert_mode,
            "ready": issue_ready,
            "read_only": True,
        }
    ], blockers


def _github_auth_status_readiness() -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    try:
        from aethos_core.providers.github.auth import GitHubAuthAdapter

        status = GitHubAuthAdapter().connection_status()
        auth = GitHubAuthAdapter().resolve_best_auth_method(operation="read_repos")
        token_configured = bool(auth.get("credential_id"))
        api_token = status.api_token if hasattr(status, "api_token") else "unknown"
        ready = token_configured and api_token not in {"missing", "invalid"}
        if not ready:
            blockers.append("github_auth_not_ready")
        return [
            {
                "status_id": "github-auth",
                "credential_configured": token_configured,
                "api_token_state": str(api_token),
                "auth_method": auth.get("method"),
                "ready": ready,
                "read_only": True,
            }
        ], blockers
    except Exception as exc:
        blockers.append("github_auth_check_failed")
        return [
            {
                "status_id": "github-auth",
                "credential_configured": False,
                "ready": False,
                "detail": str(exc)[:200],
                "read_only": True,
            }
        ], blockers


def _branch_permissions_readiness() -> tuple[list[dict[str, Any]], list[str]]:
    settings = get_settings()
    blockers: list[str] = []
    branch_enabled = bool(getattr(settings, "software_delivery_branch_orchestration_enabled", True))
    push_enabled = bool(getattr(settings, "software_delivery_github_branch_push_enabled", True))
    default_branch = str(getattr(settings, "software_delivery_github_default_branch", "main") or "main")
    ready = branch_enabled and push_enabled and SOFTWARE_DELIVERY_PHASE_2_FROZEN
    if not branch_enabled:
        blockers.append("branch_orchestration_disabled")
    if not push_enabled:
        blockers.append("branch_push_disabled")
    if not SOFTWARE_DELIVERY_PHASE_2_FROZEN:
        blockers.append("software_delivery_not_frozen")
    return [
        {
            "permission_id": "branch-permissions",
            "branch_orchestration_enabled": branch_enabled,
            "branch_push_enabled": push_enabled,
            "default_branch": default_branch,
            "phase_2_frozen": SOFTWARE_DELIVERY_PHASE_2_FROZEN,
            "ready": ready,
            "read_only": True,
        }
    ], blockers


def _workspace_readiness() -> tuple[list[dict[str, Any]], list[str]]:
    settings = get_settings()
    blockers: list[str] = []
    apply_enabled = bool(getattr(settings, "software_delivery_workspace_apply_enabled", True))
    patch_enabled = bool(getattr(settings, "software_delivery_patch_proposal_enabled", True))
    ready = apply_enabled and patch_enabled
    if not apply_enabled:
        blockers.append("workspace_apply_disabled")
    if not patch_enabled:
        blockers.append("patch_proposal_disabled")
    return [
        {
            "readiness_id": "workspace-readiness",
            "workspace_apply_enabled": apply_enabled,
            "patch_proposal_enabled": patch_enabled,
            "governed_workspace_only": True,
            "ready": ready,
            "read_only": True,
        }
    ], blockers


def _verification_command_readiness() -> tuple[list[dict[str, Any]], list[str]]:
    settings = get_settings()
    blockers: list[str] = []
    verify_enabled = bool(getattr(settings, "software_delivery_workspace_verification_enabled", True))
    require_applied = bool(getattr(settings, "software_delivery_workspace_verification_require_applied", True))
    ready = verify_enabled
    if not verify_enabled:
        blockers.append("workspace_verification_disabled")
    return [
        {
            "readiness_id": "verification-command",
            "workspace_verification_enabled": verify_enabled,
            "require_workspace_applied": require_applied,
            "command_hint": "run workspace verification",
            "ready": ready,
            "read_only": True,
        }
    ], blockers


def _pr_creation_readiness() -> tuple[list[dict[str, Any]], list[str]]:
    settings = get_settings()
    blockers: list[str] = []
    draft_enabled = bool(getattr(settings, "software_delivery_pr_draft_enabled", True))
    preflight_enabled = bool(getattr(settings, "software_delivery_github_pr_preflight_enabled", True))
    push_enabled = bool(getattr(settings, "software_delivery_github_branch_push_enabled", True))
    open_enabled = bool(getattr(settings, "software_delivery_github_pr_open_enabled", True))
    ready = draft_enabled and preflight_enabled and push_enabled and open_enabled
    if not draft_enabled:
        blockers.append("pr_draft_disabled")
    if not preflight_enabled:
        blockers.append("github_pr_preflight_disabled")
    if not open_enabled:
        blockers.append("github_pr_open_disabled")
    return [
        {
            "readiness_id": "pr-creation",
            "pr_draft_enabled": draft_enabled,
            "github_pr_preflight_enabled": preflight_enabled,
            "branch_push_enabled": push_enabled,
            "github_pr_open_enabled": open_enabled,
            "github_pr_creation_lane_enabled": GITHUB_PR_CREATION_ENABLED_FIX_125F is False,
            "merge_enabled": SOFTWARE_DELIVERY_MERGE_ENABLED,
            "ready": ready,
            "read_only": True,
        }
    ], blockers


def _mission_control_evidence_readiness(*, session_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    bundle = build_evidence_bundle(session_id=session_id)
    ready = bundle.ok
    if not ready:
        blockers.append("evidence_bundle_unavailable")
    payload = bundle.bundle if bundle.ok else {}
    return [
        {
            "readiness_id": "mission-control-evidence",
            "evidence_bundle_ok": bundle.ok,
            "section_count": len(payload.get("sections") or {}),
            "timeline_included": "timeline" in (payload.get("sections") or {}),
            "ready": ready,
            "read_only": True,
        }
    ], blockers


def _approval_friction_summary() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, phrase in enumerate(SOFTWARE_DELIVERY_APPROVAL_PHRASES, start=1):
        rows.append(
            {
                "phrase_id": f"approval-phrase-{idx}",
                "exact_phrase_required": True,
                "phrase_excerpt": phrase[:80] + ("…" if len(phrase) > 80 else ""),
                "gate_bypass": False,
                "read_only": True,
            }
        )
    rows.append(
        {
            "summary_id": "approval-friction-summary",
            "phrase_count": len(SOFTWARE_DELIVERY_APPROVAL_PHRASES),
            "github_pr_preflight_phrase_required": True,
            "github_pr_open_phrase_required": True,
            "preflight_phrase": GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE[:60] + "…",
            "open_phrase": GITHUB_PR_OPEN_APPROVAL_PHRASE[:60] + "…",
            "read_only": True,
        }
    )
    return rows


def _pilot_blocker_list(*, blockers: list[str]) -> list[dict[str, Any]]:
    if not blockers:
        return [
            {
                "blocker_id": "no-blockers",
                "detail": "No pilot blockers detected — repo may be ready for bounded pilot.",
                "severity": "none",
                "read_only": True,
            }
        ]
    return [
        {
            "blocker_id": f"blocker-{idx}",
            "code": code,
            "detail": f"Pilot preflight blocker: {code}",
            "severity": "blocking",
            "read_only": True,
        }
        for idx, code in enumerate(sorted(set(blockers)), start=1)
    ]


def _forbidden_readiness_actions() -> list[dict[str, Any]]:
    return [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_READINESS_ACTIONS
    ]


def _next_step_readiness_sequence(*, pilot_ready: bool) -> list[dict[str, Any]]:
    if pilot_ready:
        return [
            {
                "step": 1,
                "command_hint": "run pilot — explicit operator action through FIX 181 harness",
                "pilot_execution_performed": False,
                "read_only": True,
            }
        ]
    return [
        {
            "step": 1,
            "command_hint": "readiness artifact: <summary> — record repo/issue selection notes",
            "pilot_execution_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "resolve pilot blockers listed in dashboard before running pilot",
            "read_only": True,
        },
    ]


def _readiness_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    blocker_count: int,
    checks_ready: int,
    checks_total: int,
) -> list[dict[str, Any]]:
    score = 20 + int((checks_ready / max(checks_total, 1)) * 60)
    if blocker_count == 0:
        score += 15
    if _by_kind(records, "readiness_artifact"):
        score += 5
    score = min(100, score)
    label = "pilot_preflight_ready" if score >= 85 and blocker_count == 0 else "partial" if score >= 50 else "blocked"
    return [
        {
            "score_id": "repo-pilot-readiness-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "checks_ready": checks_ready,
            "checks_total": checks_total,
            "blocker_count": blocker_count,
            "readiness_not_execution": True,
            "composes_upstream_layers": True,
            "read_only": True,
        }
    ]


def _audit_replay_linkage_at_readiness(
    *,
    exported_at: str,
    session_id: str,
    plan_id: str | None,
) -> list[dict[str, Any]]:
    return [
        {
            "link_id": "repo-pilot-readiness-audit-replay",
            "timeline_link_ref": timeline_link_ref(
                lane="software_delivery",
                action="repo_pilot_readiness_dashboard",
                timestamp=exported_at,
            ),
            "replay_link_key": replay_link_key(
                source=REPO_PILOT_READINESS_DASHBOARD_ORIGIN,
                lane="software_delivery",
                action="repo_pilot_readiness_dashboard",
                timestamp=exported_at,
                anchor=plan_id or session_id,
            ),
            "read_only": True,
        }
    ]


def build_repo_pilot_readiness_dashboard(*, session_id: str) -> RepoPilotReadinessDashboardResult:
    sid = (session_id or "default").strip()[:64] or "default"

    harness_result = build_end_to_end_repo_development_pilot_harness(session_id=sid)
    harness = harness_result.end_to_end_repo_development_pilot_harness if harness_result.ok else {}

    plan_id = str(harness.get("plan_id") or "") or None
    correlation_id = str(harness.get("correlation_id") or "") or None
    exported_at = _exported_at()

    records = list_repo_pilot_readiness_dashboard_records(session_id=sid, plan_id=plan_id)
    repo_issue, repo = _resolve_repo_issue(records=records, harness=harness)

    all_blockers: list[str] = []
    check_results: list[tuple[list[dict[str, Any]], list[str]]] = [
        _repo_selection_readiness(repo=repo),
        _issue_selection_readiness(repo_issue=repo_issue),
        _github_auth_status_readiness(),
        _branch_permissions_readiness(),
        _workspace_readiness(),
        _verification_command_readiness(),
        _pr_creation_readiness(),
        _mission_control_evidence_readiness(session_id=sid),
    ]

    sections_data: dict[str, list[dict[str, Any]]] = {}
    section_keys = (
        "repo_selection_readiness",
        "issue_selection_readiness",
        "github_auth_status_readiness",
        "branch_permissions_readiness",
        "workspace_readiness",
        "verification_command_readiness",
        "pr_creation_readiness",
        "mission_control_evidence_readiness",
    )
    checks_ready = 0
    for key, (rows, blockers) in zip(section_keys, check_results, strict=True):
        sections_data[key] = rows
        all_blockers.extend(blockers)
        if rows and rows[0].get("ready"):
            checks_ready += 1

    pilot_blockers = sorted(set(all_blockers))
    pilot_preflight_ready = checks_ready == len(check_results) and not pilot_blockers

    sections = {
        "pilot_harness_upstream_read": _pilot_harness_upstream_read(harness=harness),
        **sections_data,
        "approval_friction_summary": _approval_friction_summary(),
        "pilot_blocker_list": _pilot_blocker_list(blockers=pilot_blockers),
        "audit_replay_linkage_at_readiness": _audit_replay_linkage_at_readiness(
            exported_at=exported_at,
            session_id=sid,
            plan_id=plan_id,
        ),
        "forbidden_readiness_actions": _forbidden_readiness_actions(),
        "next_step_readiness_sequence": _next_step_readiness_sequence(pilot_ready=pilot_preflight_ready),
        "readiness_integrity_scoring": _readiness_integrity_scoring(
            records=records,
            blocker_count=len(pilot_blockers),
            checks_ready=checks_ready,
            checks_total=len(check_results),
        ),
    }

    repo_pilot_readiness_dashboard: dict[str, Any] = {
        "schema_version": REPO_PILOT_READINESS_DASHBOARD_SCHEMA_VERSION,
        "fix": REPO_PILOT_READINESS_DASHBOARD_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_182,
        "execution_performed": EXECUTION_PERFORMED_FIX_182,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_182,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182,
        "pilot_execution_performed": PILOT_EXECUTION_PERFORMED_FIX_182,
        "autonomous_readiness_mutation_enabled": AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182,
        "hidden_pilot_execution_performed": HIDDEN_PILOT_EXECUTION_PERFORMED_FIX_182,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_182,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_182,
        "readiness_visibility_only": READINESS_VISIBILITY_ONLY_FIX_182,
        "merge_enabled": SOFTWARE_DELIVERY_MERGE_ENABLED,
        "deploy_enabled": SOFTWARE_DELIVERY_DEPLOY_ENABLED,
        "railway_mutation_enabled": SOFTWARE_DELIVERY_RAILWAY_MUTATION_ENABLED,
        "invariant": REPO_PILOT_READINESS_DASHBOARD_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "readiness_record_count": len(records),
        "repo_issue": repo_issue,
        "repo": repo,
        "pilot_preflight_ready": pilot_preflight_ready,
        "pilot_blocker_count": len(pilot_blockers),
        "checks_ready": checks_ready,
        "checks_total": len(check_results),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_181_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_181),
        },
        "fix_182_certification_requirements": list(FIX_182_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "repo_pilot_readiness_dashboard_cognition": True,
        "readiness_dashboard_not_pilot_execution": True,
        "repo_pilot_readiness_dashboard_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in REPO_PILOT_READINESS_DASHBOARD_PRINCIPLES
        ],
        "sources": {
            "composes_end_to_end_repo_development_pilot_harness": harness_result.ok,
            "end_to_end_repo_development_pilot_harness_fix": "FIX 181",
            "readiness_records": len(records),
        },
    }
    return RepoPilotReadinessDashboardResult(
        ok=True,
        session_id=sid,
        repo_pilot_readiness_dashboard=repo_pilot_readiness_dashboard,
        detail="Repo pilot readiness dashboard assembled (composes FIX 181 — readiness ≠ execution).",
    )
