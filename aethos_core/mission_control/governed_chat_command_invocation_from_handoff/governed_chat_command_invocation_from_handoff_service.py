# SPDX-License-Identifier: Apache-2.0
"""FIX 180 — governed chat command invocation from handoff (composes FIX 179)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_180_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_service import (
    build_frozen_gate_execution_request_adapter,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_180,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_180,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180,
    CHAT_GOVERNANCE_REQUIRED_FIX_180,
    CODE_WRITE_ENABLED_FIX_180,
    DIRECT_EXECUTION_PERFORMED_FIX_180,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
    EXECUTION_PERFORMED_FIX_180,
    FORBIDDEN_INVOCATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_180,
    GATE_EXECUTION_PERFORMED_FIX_180,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_FIX,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_INVARIANT,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_PRINCIPLES,
    GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_180,
    HANDOFF_INVOCATION_CHANNEL,
    HANDOFF_INVOCATION_ORIGIN,
    HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180,
    INVOCATION_TIER,
    LANE_ADMISSION_EXECUTED_FIX_180,
    LANE_ENTRY_EXECUTION_PERFORMED_FIX_180,
    MERGE_DEPLOY_ENABLED_FIX_180,
    MUTATION_PERFORMED_FIX_180,
    PR_ACTION_ENABLED_FIX_180,
    RAILWAY_MUTATION_ENABLED_FIX_180,
    TIER_ESCALATION_ENABLED_FIX_180,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_179,
)
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_store import (
    list_governed_chat_command_invocation_from_handoff_records,
    list_handoff_invocation_audits,
    persist_handoff_invocation_audit,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import (
    replay_link_key,
    timeline_link_ref,
)


@dataclass(frozen=True)
class GovernedChatCommandInvocationFromHandoffResult:
    ok: bool
    session_id: str
    governed_chat_command_invocation_from_handoff: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class GovernedChatCommandInvocationOutcome:
    ok: bool
    session_id: str
    frozen_chat_command: str = ""
    governed_chat_message: str = ""
    chat_intent: str = ""
    route_id: str = ""
    reply: str = ""
    audit_id: str = ""
    blockers: list[str] = field(default_factory=list)
    detail: str = ""
    chat_governance_routed: bool = False
    direct_provider_mutation: bool = False


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _execution_request_upstream_read(*, adapter: dict[str, Any]) -> list[dict[str, Any]]:
    artifact = (_sections(adapter).get("gate_execution_request_artifact") or [{}])[0]
    return [
        {
            "read_id": "fix-179-execution-request-read",
            "upstream_fix": "FIX 179",
            "execution_request_ready": adapter.get("execution_request_ready"),
            "target_gate_id": adapter.get("target_gate_id"),
            "primary_frozen_command": adapter.get("primary_frozen_command"),
            "decision_value": artifact.get("decision_value"),
            "read_only": True,
            "recomputed_by_fix_180": False,
        }
    ]


def build_exact_frozen_chat_command(*, adapter: dict[str, Any]) -> tuple[str, list[str]]:
    blockers: list[str] = []
    primary = str(adapter.get("primary_frozen_command") or "").strip()
    if not primary:
        blockers.append("primary_frozen_command_missing")
        return "", blockers

    phrase_rows = _sections(adapter).get("approval_phrase_preservation") or []
    phrase_row = phrase_rows[0] if phrase_rows else {}
    if phrase_row.get("approval_phrase_required") and not phrase_row.get("exact_approval_phrase"):
        blockers.append("approval_phrase_required_but_missing")

    lines = [primary]
    phrase = phrase_row.get("exact_approval_phrase")
    if phrase_row.get("approval_phrase_required") and phrase:
        lines.append(str(phrase).strip())
    return "\n".join(lines), blockers


def build_governed_handoff_chat_message(*, frozen_chat_command: str) -> str:
    return f"[{HANDOFF_INVOCATION_ORIGIN}]\n{frozen_chat_command.strip()}"


def _frozen_chat_command_build(*, adapter: dict[str, Any]) -> list[dict[str, Any]]:
    command, blockers = build_exact_frozen_chat_command(adapter=adapter)
    governed_message = build_governed_handoff_chat_message(frozen_chat_command=command) if command else ""
    return [
        {
            "build_id": "frozen-chat-command-build",
            "frozen_chat_command": command or None,
            "governed_chat_message": governed_message or None,
            "build_ready": bool(command) and not blockers,
            "blockers": blockers,
            "direct_execution_performed": False,
            "read_only": True,
        }
    ]


def _governed_invocation_packet(
    *,
    adapter: dict[str, Any],
    invocation_ready: bool,
    frozen_chat_command: str | None,
) -> list[dict[str, Any]]:
    return [
        {
            "packet_id": "governed-chat-command-invocation-packet",
            "target_gate_id": adapter.get("target_gate_id"),
            "frozen_chat_command": frozen_chat_command,
            "invocation_ready": invocation_ready and bool(frozen_chat_command),
            "chat_governance_required": CHAT_GOVERNANCE_REQUIRED_FIX_180,
            "direct_provider_mutation_performed": False,
            "direct_execution_performed": False,
            "hidden_command_execution_performed": False,
            "gate_bypass": False,
            "approval_bypass": False,
            "detail": "Invocation packet — routes through resolve_chat_turn governance only.",
            "read_only": True,
        }
    ]


def _approval_gate_preservation(*, adapter: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(adapter).get("approval_phrase_preservation") or []:
        if row.get("phrase_id"):
            rows.append({**row, "upstream_fix": "FIX 179", "read_only": True})
    if not rows:
        rows.append(
            {
                "phrase_id": "no-phrases",
                "detail": "No approval phrase preservation rows from upstream FIX 179.",
                "read_only": True,
            }
        )
    return rows


def _missing_prerequisites_at_invocation(*, adapter: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(adapter).get("missing_prerequisites_in_request") or []:
        if row.get("prerequisite_id"):
            rows.append({**row, "upstream_fix": "FIX 179", "read_only": True})
    if not rows:
        rows.append(
            {
                "prerequisite_id": "no-prerequisites",
                "detail": "No prerequisite rows from upstream FIX 179 execution request.",
                "read_only": True,
            }
        )
    return rows[:16]


def _risk_blast_radius_at_invocation(*, adapter: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _sections(adapter).get("risk_blast_radius_summary") or []:
        if row.get("summary_id"):
            rows.append({**row, "upstream_fix": "FIX 179", "read_only": True})
    if not rows:
        rows.append(
            {
                "summary_id": "default-blast-radius",
                "tier": INVOCATION_TIER,
                "detail": "Bounded Tier 1–2 invocation — chat governance route only.",
                "read_only": True,
            }
        )
    return rows


def _audit_replay_linkage(
    *,
    adapter: dict[str, Any],
    exported_at: str,
) -> list[dict[str, Any]]:
    gate_id = adapter.get("target_gate_id")
    plan_id = str(adapter.get("plan_id") or "")
    session_id = str(adapter.get("session_id") or "")
    upstream = (_sections(adapter).get("audit_replay_linkage") or [{}])[0]
    timeline_ref = timeline_link_ref(
        lane="software_delivery",
        action=f"handoff_invocation:{gate_id or 'pending'}",
        timestamp=exported_at,
    )
    replay_key = replay_link_key(
        source=HANDOFF_INVOCATION_ORIGIN,
        lane="software_delivery",
        action=f"handoff_invocation:{gate_id or 'pending'}",
        timestamp=exported_at,
        anchor=plan_id or session_id,
    )
    return [
        {
            "link_id": "handoff-invocation-audit-replay",
            "timeline_link_ref": timeline_ref,
            "replay_link_key": replay_key,
            "upstream_timeline_link_ref": upstream.get("timeline_link_ref"),
            "upstream_replay_link_key": upstream.get("replay_link_key"),
            "mission_link_ref": "mission:start",
            "plan_id": plan_id or None,
            "session_id": session_id,
            "gate_id": gate_id,
            "detail": "Audit and replay linkage for governed handoff chat invocation.",
            "read_only": True,
        }
    ]


def _chat_origin_logging(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "origin_log_note")]
    audits = list_handoff_invocation_audits(limit=5)
    rows: list[dict[str, Any]] = list(stored)
    rows.append(
        {
            "origin_id": "handoff-invocation-origin",
            "handoff_invocation_origin": HANDOFF_INVOCATION_ORIGIN,
            "handoff_invocation_channel": HANDOFF_INVOCATION_CHANNEL,
            "recent_invocation_audit_count": len(audits),
            "detail": "Chat/UI origin logged for governed handoff invocation.",
            "read_only": True,
        }
    )
    return rows


def _forbidden_invocation_actions() -> list[dict[str, Any]]:
    return [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_INVOCATION_ACTIONS
    ]


def _next_step_invocation_sequence(
    *,
    invocation_ready: bool,
    frozen_chat_command: str | None,
) -> list[dict[str, Any]]:
    if not invocation_ready or not frozen_chat_command:
        return [
            {
                "step": 1,
                "command_hint": "frozen gate execution request — complete FIX 179 execution request",
                "direct_execution_performed": False,
                "read_only": True,
            }
        ]
    return [
        {
            "step": 1,
            "command_hint": "handoff invocation artifact: <summary> — persist invocation record",
            "direct_execution_performed": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "invoke handoff command — routes through resolve_chat_turn governance",
            "gate_bypass": False,
            "read_only": True,
        },
    ]


def _invocation_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    invocation_ready: bool,
    command_built: bool,
) -> list[dict[str, Any]]:
    score = 15 + (25 if invocation_ready else 0) + (20 if command_built else 0)
    if _by_kind(records, "invocation_artifact"):
        score += 10
    if list_handoff_invocation_audits(limit=1):
        score += 10
    score = min(100, score)
    label = "invocation_ready" if score >= 75 else "partial" if score >= 45 else "blocked"
    return [
        {
            "score_id": "governed-chat-command-invocation-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_180,
            "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
            "composes_upstream_layers": True,
            "detail": "Invocation integrity — composes FIX 179 through chat governance only.",
            "read_only": True,
        }
    ]


def build_governed_chat_command_invocation_from_handoff(
    *, session_id: str
) -> GovernedChatCommandInvocationFromHandoffResult:
    sid = (session_id or "default").strip()[:64] or "default"

    adapter_result = build_frozen_gate_execution_request_adapter(session_id=sid)
    adapter = adapter_result.frozen_gate_execution_request_adapter if adapter_result.ok else {}

    plan_id = str(adapter.get("plan_id") or "") or None
    correlation_id = str(adapter.get("correlation_id") or "") or None
    exported_at = _exported_at()

    records = list_governed_chat_command_invocation_from_handoff_records(session_id=sid, plan_id=plan_id)
    request_ready = bool(adapter.get("execution_request_ready")) and adapter_result.ok

    frozen_chat_command, build_blockers = build_exact_frozen_chat_command(adapter=adapter)
    command_built = bool(frozen_chat_command) and not build_blockers
    invocation_ready = request_ready and command_built

    sections = {
        "execution_request_upstream_read": _execution_request_upstream_read(adapter=adapter),
        "frozen_chat_command_build": _frozen_chat_command_build(adapter=adapter),
        "governed_invocation_packet": _governed_invocation_packet(
            adapter=adapter,
            invocation_ready=invocation_ready,
            frozen_chat_command=frozen_chat_command or None,
        ),
        "approval_gate_preservation": _approval_gate_preservation(adapter=adapter),
        "missing_prerequisites_at_invocation": _missing_prerequisites_at_invocation(adapter=adapter),
        "risk_blast_radius_at_invocation": _risk_blast_radius_at_invocation(adapter=adapter),
        "audit_replay_linkage_at_invocation": _audit_replay_linkage(adapter=adapter, exported_at=exported_at),
        "chat_origin_logging": _chat_origin_logging(records=records),
        "forbidden_invocation_actions": _forbidden_invocation_actions(),
        "next_step_invocation_sequence": _next_step_invocation_sequence(
            invocation_ready=invocation_ready,
            frozen_chat_command=frozen_chat_command or None,
        ),
        "invocation_integrity_scoring": _invocation_integrity_scoring(
            records=records,
            invocation_ready=invocation_ready,
            command_built=command_built,
        ),
    }

    governed_chat_command_invocation_from_handoff: dict[str, Any] = {
        "schema_version": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_SCHEMA_VERSION,
        "fix": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_180,
        "execution_performed": EXECUTION_PERFORMED_FIX_180,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_180,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
        "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_180,
        "hidden_command_execution_performed": HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_180,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_180,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_180,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_180,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_180,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_180,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_180,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_180,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_180,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_180,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_180,
        "chat_governance_required": CHAT_GOVERNANCE_REQUIRED_FIX_180,
        "invariant": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "invocation_record_count": len(records),
        "target_gate_id": adapter.get("target_gate_id"),
        "frozen_chat_command": frozen_chat_command or None,
        "invocation_tier": INVOCATION_TIER if invocation_ready else None,
        "invocation_ready": invocation_ready,
        "execution_request_ready_upstream": adapter.get("execution_request_ready"),
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_179_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_179),
        },
        "fix_180_certification_requirements": list(FIX_180_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "governed_chat_command_invocation_from_handoff_cognition": True,
        "handoff_invocation_not_direct_execution": True,
        "governed_chat_command_invocation_from_handoff_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_PRINCIPLES
        ],
        "sources": {
            "composes_frozen_gate_execution_request_adapter": adapter_result.ok,
            "frozen_gate_execution_request_adapter_fix": "FIX 179",
            "invocation_records": len(records),
            "handoff_invocation_audits": len(list_handoff_invocation_audits(session_id=sid)),
        },
    }
    return GovernedChatCommandInvocationFromHandoffResult(
        ok=True,
        session_id=sid,
        governed_chat_command_invocation_from_handoff=governed_chat_command_invocation_from_handoff,
        detail="Governed chat command invocation from handoff assembled (composes FIX 179 — invocation ≠ direct execution).",
    )


def invoke_governed_chat_command_from_handoff(*, session_id: str) -> GovernedChatCommandInvocationOutcome:
    sid = (session_id or "default").strip()[:64] or "default"
    package = build_governed_chat_command_invocation_from_handoff(session_id=sid)
    adapter_view = package.governed_chat_command_invocation_from_handoff

    if not package.ok or not adapter_view.get("invocation_ready"):
        blockers = ["invocation_not_ready"]
        audit = persist_handoff_invocation_audit(
            {
                "session_id": sid,
                "outcome": "blocked",
                "blockers": blockers,
                "invocation_ready": False,
            }
        )
        return GovernedChatCommandInvocationOutcome(
            ok=False,
            session_id=sid,
            blockers=blockers,
            audit_id=str(audit.get("audit_id") or ""),
            detail="Handoff invocation blocked — execution request not ready.",
        )

    frozen_chat_command = str(adapter_view.get("frozen_chat_command") or "")
    governed_message = build_governed_handoff_chat_message(frozen_chat_command=frozen_chat_command)

    from aethos_core.chat.service import resolve_chat_turn

    turn = resolve_chat_turn(
        governed_message,
        session_id=sid,
        channel=HANDOFF_INVOCATION_CHANNEL,
        apply_relational_layer=False,
    )
    meta = turn.meta or {}
    route_id = str(meta.get("route_id") or "")
    lane_mutation = str(meta.get("mutation_performed", "false")).lower() == "true"

    audit = persist_handoff_invocation_audit(
        {
            "session_id": sid,
            "plan_id": adapter_view.get("plan_id"),
            "correlation_id": adapter_view.get("correlation_id"),
            "target_gate_id": adapter_view.get("target_gate_id"),
            "frozen_chat_command": frozen_chat_command,
            "governed_chat_message": governed_message,
            "chat_intent": turn.intent,
            "route_id": route_id,
            "outcome": "routed",
            "chat_governance_routed": True,
            "direct_provider_mutation": False,
            "lane_mutation_performed_by_chat_route": lane_mutation,
            "reply_excerpt": (turn.reply or "")[:500],
            "blockers": [],
        }
    )

    return GovernedChatCommandInvocationOutcome(
        ok=True,
        session_id=sid,
        frozen_chat_command=frozen_chat_command,
        governed_chat_message=governed_message,
        chat_intent=turn.intent or "",
        route_id=route_id,
        reply=turn.reply or "",
        audit_id=str(audit.get("audit_id") or ""),
        detail="Handoff command routed through resolve_chat_turn governance.",
        chat_governance_routed=True,
        direct_provider_mutation=False,
    )
