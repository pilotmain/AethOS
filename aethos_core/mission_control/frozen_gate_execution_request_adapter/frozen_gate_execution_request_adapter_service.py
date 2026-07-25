# SPDX-License-Identifier: Apache-2.0
"""FIX 179 — frozen gate execution request adapter (composes FIX 178)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_179_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_179,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_179,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179,
    CODE_WRITE_ENABLED_FIX_179,
    COMMAND_EXECUTION_PERFORMED_FIX_179,
    EXECUTION_PERFORMED_FIX_179,
    EXECUTION_REQUEST_TIER,
    FORBIDDEN_REQUEST_ACTIONS,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_FIX,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_INVARIANT,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_PRINCIPLES,
    FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_SCHEMA_VERSION,
    FROZEN_SOFTWARE_DELIVERY_GATES,
    GATE_BLAST_RADIUS_SUMMARY,
    GATE_BYPASS_ENABLED_FIX_179,
    GATE_EXECUTION_PERFORMED_FIX_179,
    GATE_FROZEN_COMMAND_MAP,
    GOVERNANCE_MUTATION_PERFORMED_FIX_179,
    LANE_ADMISSION_EXECUTED_FIX_179,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_179,
    MERGE_DEPLOY_ENABLED_FIX_179,
    MUTATION_PERFORMED_FIX_179,
    PR_ACTION_ENABLED_FIX_179,
    RAILWAY_MUTATION_ENABLED_FIX_179,
    TIER_ESCALATION_ENABLED_FIX_179,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_178,
)
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
    list_frozen_gate_execution_request_adapter_records,
)
from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_service import (
    build_frozen_gate_intake_preview,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import (
    replay_link_key,
    timeline_link_ref,
)


@dataclass(frozen=True)
class FrozenGateExecutionRequestAdapterResult:
    ok: bool
    session_id: str
    frozen_gate_execution_request_adapter: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _intake_preview_packet(preview: dict[str, Any]) -> dict[str, Any]:
    rows = _sections(preview).get("intake_preview_packet") or []
    return rows[0] if rows else {}


def _intake_preview_upstream_read(*, preview: dict[str, Any]) -> list[dict[str, Any]]:
    packet = _intake_preview_packet(preview)
    upstream = (_sections(preview).get("handoff_upstream_read") or [{}])[0]
    return [
        {
            "read_id": "fix-178-intake-preview-read",
            "upstream_fix": "FIX 178",
            "intake_preview_ready": preview.get("intake_preview_ready"),
            "target_gate_id": preview.get("target_gate_id"),
            "handoff_ready_upstream": preview.get("handoff_ready_upstream"),
            "decision_value": packet.get("decision_value") or upstream.get("decision_value"),
            "read_only": True,
            "recomputed_by_fix_179": False,
        }
    ]


def _frozen_gate_command_mapping(
    *,
    preview: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "command_mapping_note")]
    gate_id = preview.get("target_gate_id")
    rows: list[dict[str, Any]] = list(stored)
    mapping = GATE_FROZEN_COMMAND_MAP.get(str(gate_id or ""))
    if gate_id and mapping:
        rows.append(
            {
                "mapping_id": f"map-{gate_id}",
                "gate_id": gate_id,
                "primary_frozen_command": mapping.get("primary_frozen_command"),
                "software_delivery_route": mapping.get("software_delivery_route"),
                "frozen_software_delivery_gate": gate_id in FROZEN_SOFTWARE_DELIVERY_GATES,
                "command_execution_performed": False,
                "gate_execution_performed": False,
                "read_only": True,
            }
        )
    if not rows:
        rows.append(
            {
                "mapping_id": "pending-mapping",
                "detail": "Frozen gate command mapping pending FIX 178 intake preview.",
                "read_only": True,
            }
        )
    return rows


def _resolve_approval_phrase(contract_key: str) -> str | None:
    from aethos_core.software_delivery.github_pr_preflight_contract import (
        GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
    )
    from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
    from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_APPROVAL_PHRASE
    from aethos_core.software_delivery.workspace_application_contract import (
        WORKSPACE_APPLY_APPROVAL_PHRASE,
    )

    phrases = {
        "PLANNING_APPROVAL_PHRASE": PLANNING_APPROVAL_PHRASE,
        "PATCH_PROPOSAL_APPROVAL_PHRASE": PATCH_PROPOSAL_APPROVAL_PHRASE,
        "WORKSPACE_APPLY_APPROVAL_PHRASE": WORKSPACE_APPLY_APPROVAL_PHRASE,
        "GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE": GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
    }
    return phrases.get(contract_key)


def _approval_phrase_preservation(*, gate_id: str | None) -> list[dict[str, Any]]:
    mapping = GATE_FROZEN_COMMAND_MAP.get(str(gate_id or ""))
    if not mapping:
        return [
            {
                "phrase_id": "pending-phrases",
                "detail": "Approval phrase preservation pending target frozen gate.",
                "read_only": True,
            }
        ]
    phrase_required = bool(mapping.get("approval_phrase_required"))
    contract_key = str(mapping.get("approval_phrase_contract") or "")
    phrase = _resolve_approval_phrase(contract_key) if contract_key else None
    rows: list[dict[str, Any]] = [
        {
            "phrase_id": f"preserve-{gate_id}",
            "gate_id": gate_id,
            "approval_phrase_required": phrase_required,
            "approval_phrase_contract": contract_key or None,
            "exact_approval_phrase": phrase,
            "approval_bypass": False,
            "gate_bypass": False,
            "detail": "Existing frozen approval phrases preserved — adapter does not mutate phrases.",
            "read_only": True,
        }
    ]
    if phrase_required and not phrase:
        rows.append(
            {
                "phrase_id": "phrase-contract-missing",
                "detail": f"Approval contract `{contract_key}` referenced but phrase unresolved.",
                "read_only": True,
            }
        )
    return rows


def _missing_prerequisites_in_request(*, preview: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(preview).get("missing_gate_prerequisites") or []:
        if row.get("prerequisite_id"):
            rows.append(
                {
                    **row,
                    "upstream_fix": "FIX 178",
                    "included_in_execution_request": True,
                    "read_only": True,
                }
            )
    if not rows:
        rows.append(
            {
                "prerequisite_id": "no-prerequisites",
                "detail": "No prerequisite rows from upstream FIX 178 intake preview.",
                "read_only": True,
            }
        )
    return rows[:16]


def _risk_blast_radius_summary(*, preview: dict[str, Any], gate_id: str | None) -> list[dict[str, Any]]:
    gate_summary = GATE_BLAST_RADIUS_SUMMARY.get(str(gate_id or ""), {})
    missing = [
        r
        for r in _sections(preview).get("missing_gate_prerequisites") or []
        if r.get("satisfied") is False
    ]
    return [
        {
            "summary_id": "execution-request-blast-radius",
            "gate_id": gate_id,
            "tier": gate_summary.get("tier") or EXECUTION_REQUEST_TIER,
            "scope": gate_summary.get("scope") or "software_delivery_bounded",
            "detail": gate_summary.get("detail")
            or "Bounded Tier 1–2 execution request — no merge, deploy, or Railway mutation.",
            "missing_prerequisite_count": len(missing),
            "intake_preview_ready": preview.get("intake_preview_ready"),
            "command_execution_performed": False,
            "read_only": True,
        }
    ]


def _audit_replay_linkage(
    *,
    preview: dict[str, Any],
    gate_id: str | None,
    exported_at: str,
) -> list[dict[str, Any]]:
    plan_id = str(preview.get("plan_id") or "")
    correlation_id = str(preview.get("correlation_id") or "")
    session_id = str(preview.get("session_id") or "")
    lane = "software_delivery"
    action = f"gate_execution_request:{gate_id or 'pending'}"
    timeline_ref = timeline_link_ref(lane=lane, action=action, timestamp=exported_at)
    replay_key = replay_link_key(
        source="frozen_gate_execution_request_adapter",
        lane=lane,
        action=action,
        timestamp=exported_at,
        anchor=plan_id or session_id,
    )
    return [
        {
            "link_id": "audit-replay-linkage",
            "timeline_link_ref": timeline_ref,
            "replay_link_key": replay_key,
            "mission_link_ref": "mission:start",
            "plan_id": plan_id or None,
            "correlation_id": correlation_id or None,
            "session_id": session_id,
            "gate_id": gate_id,
            "detail": "Audit and replay linkage for governed handoff to frozen lane command.",
            "read_only": True,
        }
    ]


def _gate_execution_request_artifact(
    *,
    preview: dict[str, Any],
    gate_id: str | None,
    primary_command: str | None,
    request_ready: bool,
) -> list[dict[str, Any]]:
    packet = _intake_preview_packet(preview)
    return [
        {
            "artifact_id": "frozen-gate-execution-request",
            "target_gate_id": gate_id,
            "primary_frozen_command": primary_command,
            "decision_value": packet.get("decision_value"),
            "execution_request_ready": request_ready and bool(primary_command) and bool(gate_id),
            "command_execution_performed": False,
            "gate_execution_performed": False,
            "lane_entry_execution_performed": False,
            "approval_bypass": False,
            "gate_bypass": False,
            "detail": "Execution request artifact — operator invokes frozen command via normal chat governance.",
            "read_only": True,
        }
    ]


def _forbidden_request_actions() -> list[dict[str, Any]]:
    return [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_REQUEST_ACTIONS
    ]


def _next_step_request_sequence(
    *,
    request_ready: bool,
    primary_command: str | None,
) -> list[dict[str, Any]]:
    if not request_ready or not primary_command:
        return [
            {
                "step": 1,
                "command_hint": "frozen gate intake preview — complete FIX 178 intake preview",
                "command_execution_performed": False,
                "read_only": True,
            }
        ]
    return [
        {
            "step": 1,
            "command_hint": "gate execution request artifact: <summary> — persist request record",
            "command_execution_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": f"operator invokes frozen command `{primary_command}` via normal chat governance route",
            "approval_bypass": False,
            "gate_bypass": False,
            "read_only": True,
        },
    ]


def _request_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    request_ready: bool,
    gate_identified: bool,
    command_mapped: bool,
) -> list[dict[str, Any]]:
    score = 15 + (25 if request_ready else 0) + (20 if gate_identified else 0)
    score += 20 if command_mapped else 0
    if _by_kind(records, "execution_request_artifact"):
        score += 10
    score = min(100, score)
    label = "request_ready" if score >= 75 else "partial" if score >= 45 else "blocked"
    return [
        {
            "score_id": "frozen-gate-execution-request-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "command_execution_performed": COMMAND_EXECUTION_PERFORMED_FIX_179,
            "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_179,
            "composes_upstream_layers": True,
            "detail": "Execution request integrity — composes FIX 178 without command execution.",
            "read_only": True,
        }
    ]


def build_frozen_gate_execution_request_adapter(
    *, session_id: str
) -> FrozenGateExecutionRequestAdapterResult:
    sid = (session_id or "default").strip()[:64] or "default"

    preview_result = build_frozen_gate_intake_preview(session_id=sid)
    preview = preview_result.frozen_gate_intake_preview if preview_result.ok else {}

    plan_id = str(preview.get("plan_id") or "") or None
    correlation_id = str(preview.get("correlation_id") or "") or None
    exported_at = _exported_at()

    records = list_frozen_gate_execution_request_adapter_records(session_id=sid, plan_id=plan_id)
    intake_preview_ready = bool(preview.get("intake_preview_ready")) and preview_result.ok

    gate_id = preview.get("target_gate_id")
    gate_identified = bool(gate_id)
    mapping = GATE_FROZEN_COMMAND_MAP.get(str(gate_id or ""))
    primary_command = str(mapping.get("primary_frozen_command") or "") if mapping else None
    command_mapped = bool(primary_command)

    request_ready = intake_preview_ready and gate_identified and command_mapped

    sections = {
        "intake_preview_upstream_read": _intake_preview_upstream_read(preview=preview),
        "frozen_gate_command_mapping": _frozen_gate_command_mapping(preview=preview, records=records),
        "gate_execution_request_artifact": _gate_execution_request_artifact(
            preview=preview,
            gate_id=gate_id,
            primary_command=primary_command,
            request_ready=request_ready,
        ),
        "approval_phrase_preservation": _approval_phrase_preservation(gate_id=gate_id),
        "missing_prerequisites_in_request": _missing_prerequisites_in_request(preview=preview),
        "risk_blast_radius_summary": _risk_blast_radius_summary(preview=preview, gate_id=gate_id),
        "audit_replay_linkage": _audit_replay_linkage(
            preview=preview,
            gate_id=gate_id,
            exported_at=exported_at,
        ),
        "forbidden_request_actions": _forbidden_request_actions(),
        "next_step_request_sequence": _next_step_request_sequence(
            request_ready=request_ready,
            primary_command=primary_command,
        ),
        "request_integrity_scoring": _request_integrity_scoring(
            records=records,
            request_ready=request_ready,
            gate_identified=gate_identified,
            command_mapped=command_mapped,
        ),
    }

    frozen_gate_execution_request_adapter: dict[str, Any] = {
        "schema_version": FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_SCHEMA_VERSION,
        "fix": FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_179,
        "execution_performed": EXECUTION_PERFORMED_FIX_179,
        "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_179,
        "command_execution_performed": COMMAND_EXECUTION_PERFORMED_FIX_179,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_179,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_179,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_179,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_179,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_179,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_179,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_179,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_179,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_179,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_179,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_179,
        "invariant": FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "execution_request_record_count": len(records),
        "target_gate_id": gate_id,
        "primary_frozen_command": primary_command,
        "execution_request_tier": EXECUTION_REQUEST_TIER if request_ready else None,
        "execution_request_ready": request_ready,
        "intake_preview_ready_upstream": preview.get("intake_preview_ready"),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_178_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_178),
        },
        "fix_179_certification_requirements": list(FIX_179_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "frozen_gate_execution_request_adapter_cognition": True,
        "execution_request_not_command_execution": True,
        "frozen_gate_execution_request_adapter_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_PRINCIPLES
        ],
        "sources": {
            "composes_frozen_gate_intake_preview": preview_result.ok,
            "frozen_gate_intake_preview_fix": "FIX 178",
            "execution_request_records": len(records),
        },
    }
    return FrozenGateExecutionRequestAdapterResult(
        ok=True,
        session_id=sid,
        frozen_gate_execution_request_adapter=frozen_gate_execution_request_adapter,
        detail="Frozen gate execution request adapter assembled (composes FIX 178 — execution request ≠ execution).",
    )
