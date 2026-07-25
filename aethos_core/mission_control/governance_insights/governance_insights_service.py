# SPDX-License-Identifier: Apache-2.0
"""FIX 143 — build meta-governance insights (read-only)."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_insights.governance_insights_collectors import collect_governance_signals
from aethos_core.mission_control.governance_insights.governance_insights_contract import (
    AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_143,
    GOVERNANCE_INSIGHTS_FIX,
    GOVERNANCE_INSIGHTS_INVARIANT,
    GOVERNANCE_INSIGHTS_SCHEMA_VERSION,
    GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143,
    INSIGHT_EXECUTABLE,
    MUTATION_PERFORMED_FIX_143,
    POLICY_AUTO_TUNING_ENABLED_FIX_143,
)


@dataclass(frozen=True)
class GovernanceInsightsResult:
    ok: bool
    session_id: str
    insights: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _insight(*, kind: str, insight: str, severity: str = "medium", **extra: Any) -> dict[str, Any]:
    return {
        "kind": kind,
        "insight": insight,
        "severity": severity,
        "executable": INSIGHT_EXECUTABLE,
        "read_only": True,
        **extra,
    }


def _rec(*, recommendation: str, rationale: str = "", priority: str = "medium") -> dict[str, Any]:
    return {
        "recommendation": recommendation,
        "rationale": rationale,
        "priority": priority,
        "executable": INSIGHT_EXECUTABLE,
        "policy_auto_tuning": False,
        "read_only": True,
    }


def _approval_bottlenecks(signals: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    gate_counter: Counter[str] = signals.get("gate_counter") or Counter()
    inbox = signals.get("approval_inbox") or {}
    pending = len(inbox.get("items") or [])

    for gate, count in gate_counter.most_common(8):
        if count < 2 and pending < 2:
            continue
        severity = "high" if count >= 5 else "medium"
        out.append(
            _insight(
                kind="approval_bottleneck",
                insight=f"Gate `{gate}` appears in {count} approval audit(s) — potential bottleneck.",
                severity=severity,
                gate_id=gate,
                audit_count=count,
            )
        )

    if pending >= 3:
        out.append(
            _insight(
                kind="approval_bottleneck",
                insight=f"{pending} pending inbox item(s) in focal session — operator queue may be slow.",
                severity="high",
                pending_count=pending,
            )
        )
    return out


def _governance_friction(signals: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    org = (signals.get("cross_session_memory") or {}).get("organizational_memory") or {}
    for row in org.get("historical_blockers") or []:
        if not row.get("cross_session"):
            continue
        out.append(
            _insight(
                kind="governance_friction",
                insight=f"Cross-session blocker recurrence: `{row.get('blocker', '')[:80]}` (×{row.get('occurrences')}).",
                severity="high",
                blocker=row.get("blocker"),
            )
        )

    view_only = 0
    for item in (signals.get("approval_inbox") or {}).get("items") or []:
        if not item.get("ui_approval_eligible"):
            view_only += 1
    if view_only:
        out.append(
            _insight(
                kind="governance_friction",
                insight=f"{view_only} view-only gate(s) require chat governance — UI cannot clear (by design).",
                severity="medium",
                view_only_count=view_only,
            )
        )
    return out


def _rollback_patterns(signals: dict[str, Any]) -> list[dict[str, Any]]:
    rollbacks = signals.get("rollbacks") or []
    out: list[dict[str, Any]] = []
    if rollbacks:
        out.append(
            _insight(
                kind="rollback_pattern",
                insight=f"{len(rollbacks)} production rollback escalation record(s) in journal — review rollback posture.",
                severity="high" if len(rollbacks) >= 3 else "medium",
                record_count=len(rollbacks),
            )
        )
    for rb in rollbacks[:5]:
        out.append(
            _insight(
                kind="rollback_pattern",
                insight=f"Rollback escalation observed: {rb.get('execution_id') or rb.get('_source_file', 'record')}",
                severity="medium",
                recorded_at=rb.get("recorded_at"),
            )
        )
    return out


def _verification_gap_insights(signals: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rec in signals.get("memory_records") or []:
        gates = len(rec.get("gate_keys") or [])
        stats = rec.get("graph_stats") or {}
        nodes_by_kind = stats.get("nodes_by_kind") or {}
        ver = int(nodes_by_kind.get("verification") or 0)
        if gates >= 3 and ver == 0:
            out.append(
                _insight(
                    kind="verification_gap",
                    insight=(
                        f"Session `{rec.get('session_id')}` plan `{rec.get('plan_id')}` has {gates} gates "
                        "but no verification nodes in graph — workspace_verify may be lagging."
                    ),
                    severity="high",
                    session_id=rec.get("session_id"),
                    plan_id=rec.get("plan_id"),
                )
            )
    return out[:10]


def _approval_chain_inefficiencies(signals: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    outcome_counter: Counter[str] = signals.get("outcome_counter") or Counter()
    failures = sum(
        outcome_counter.get(k, 0) for k in ("failed", "error", "blocked", "replay_protected") if k in outcome_counter
    )
    successes = sum(outcome_counter.get(k, 0) for k in ("success", "gate_already_cleared"))

    if failures > successes and failures >= 2:
        out.append(
            _insight(
                kind="approval_chain_inefficiency",
                insight=f"Approval outcomes skew negative ({failures} non-success vs {successes} success) — review phrase/gate alignment.",
                severity="high",
                failures=failures,
                successes=successes,
            )
        )

    record_gates: Counter[str] = signals.get("record_gate_counter") or Counter()
    for gate, count in record_gates.most_common(5):
        if count >= 3:
            out.append(
                _insight(
                    kind="approval_chain_inefficiency",
                    insight=f"Gate `{gate}` repeated across {count} persisted memory records — possible re-approval loop.",
                    severity="medium",
                    gate_id=gate,
                    repeat_count=count,
                )
            )
    return out


def _high_risk_rollout_sequences(signals: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    open_incidents = [
        i
        for i in signals.get("incidents") or []
        if str(i.get("status") or "").lower() not in {"closed", "resolved"}
    ]
    risky_stages = {"canary", "promote", "production", "rollback", "incident"}
    for roll in signals.get("rollouts") or []:
        stage = str(roll.get("current_stage") or "").lower()
        if any(r in stage for r in risky_stages) or open_incidents:
            out.append(
                _insight(
                    kind="high_risk_rollout_sequence",
                    insight=(
                        f"Rollout stage `{roll.get('current_stage')}` with "
                        f"{len(open_incidents)} open incident(s) — elevated governance caution."
                    ),
                    severity="critical" if open_incidents else "high",
                    execution_id=roll.get("execution_id"),
                    open_incidents=len(open_incidents),
                )
            )
    return out[:8]


def _governance_health_metrics(signals: dict[str, Any]) -> dict[str, Any]:
    audits = signals.get("audits") or []
    records = signals.get("memory_records") or []
    inbox = signals.get("approval_inbox") or {}
    pending = len(inbox.get("items") or [])
    eligible = sum(1 for i in inbox.get("items") or [] if i.get("ui_approval_eligible"))

    friction_score = min(100, len(signals.get("rollbacks") or []) * 15 + pending * 5)
    coverage_score = min(100, len(records) * 10 + len(audits))
    health = max(0, 100 - friction_score)

    return {
        "governance_health_score": health,
        "audit_events_observed": len(audits),
        "persisted_memory_records": len(records),
        "pending_approvals_focal_session": pending,
        "ui_eligible_pending": eligible,
        "rollback_escalations_observed": len(signals.get("rollbacks") or []),
        "rollout_records_observed": len(signals.get("rollouts") or []),
        "read_only": True,
        "note": "Heuristic meta-governance metrics — not policy enforcement",
    }


def _operator_workload_heatmap(signals: dict[str, Any]) -> list[dict[str, Any]]:
    heatmap: list[dict[str, Any]] = []
    session_load: Counter[str] = signals.get("session_approval_load") or Counter()
    for session, count in session_load.most_common(12):
        intensity = "high" if count >= 8 else "medium" if count >= 4 else "low"
        heatmap.append(
            {
                "session_id": session,
                "approval_audit_events": count,
                "intensity": intensity,
                "read_only": True,
            }
        )
    focal = str(signals.get("session_id") or "")
    if focal and focal not in {h["session_id"] for h in heatmap}:
        heatmap.insert(
            0,
            {
                "session_id": focal,
                "approval_audit_events": session_load.get(focal, 0),
                "intensity": "focal",
                "read_only": True,
            },
        )
    return heatmap


def _mission_completion_latency(signals: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for plan_id, timestamps in (signals.get("plan_record_timestamps") or {}).items():
        if len(timestamps) < 2:
            continue
        ordered = sorted(timestamps)
        latency_sec = ordered[-1] - ordered[0]
        hours = latency_sec / 3600.0
        out.append(
            {
                "plan_id": plan_id,
                "record_snapshots": len(timestamps),
                "latency_hours": round(hours, 2),
                "latency_seconds": round(latency_sec, 1),
                "read_only": True,
                "note": "Time between first and last persisted memory snapshot for plan",
            }
        )
    out.sort(key=lambda r: -float(r.get("latency_hours") or 0))
    return out[:15]


def _meta_recommendations(insights: dict[str, Any]) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    health = insights.get("governance_health_metrics") or {}
    if int(health.get("governance_health_score") or 100) < 70:
        recs.append(
            _rec(
                recommendation="Governance health score is degraded — prioritize approval inbox triage and incident review.",
                rationale=f"score={health.get('governance_health_score')}",
                priority="high",
            )
        )
    if insights.get("approval_bottlenecks"):
        recs.append(
            _rec(
                recommendation="Review top bottleneck gates in operator guidance — do not auto-tune policy.",
                rationale="FIX 143 insight only",
                priority="medium",
            )
        )
    if insights.get("high_risk_rollout_sequences"):
        recs.append(
            _rec(
                recommendation="Pause promotion thinking until rollout + incident lanes are reconciled (operator decision).",
                rationale="High-risk rollout sequence detected",
                priority="critical",
            )
        )
    if not recs:
        recs.append(
            _rec(
                recommendation="Governance telemetry baseline healthy — continue periodic meta-governance review.",
                rationale="No critical meta-governance signals",
                priority="low",
            )
        )
    return recs


def build_governance_insights(*, session_id: str) -> GovernanceInsightsResult:
    sid = (session_id or "default").strip()[:64] or "default"
    signals = collect_governance_signals(session_id=sid)

    insight_sections = {
        "approval_bottlenecks": _approval_bottlenecks(signals),
        "governance_friction": _governance_friction(signals),
        "rollback_patterns": _rollback_patterns(signals),
        "verification_gaps": _verification_gap_insights(signals),
        "approval_chain_inefficiencies": _approval_chain_inefficiencies(signals),
        "high_risk_rollout_sequences": _high_risk_rollout_sequences(signals),
        "governance_health_metrics": _governance_health_metrics(signals),
        "operator_workload_heatmap": _operator_workload_heatmap(signals),
        "mission_completion_latency": _mission_completion_latency(signals),
    }

    all_insights: list[dict[str, Any]] = []
    for key, val in insight_sections.items():
        if key == "governance_health_metrics":
            continue
        if isinstance(val, list):
            all_insights.extend(val)

    payload: dict[str, Any] = {
        "schema_version": GOVERNANCE_INSIGHTS_SCHEMA_VERSION,
        "fix": GOVERNANCE_INSIGHTS_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_143,
        "policy_auto_tuning_enabled": POLICY_AUTO_TUNING_ENABLED_FIX_143,
        "governance_self_modification_enabled": GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143,
        "autonomous_optimization_enabled": AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_143,
        "invariant": GOVERNANCE_INSIGHTS_INVARIANT,
        "session_id": sid,
        "insights": insight_sections,
        "insight_count": len(all_insights),
        "recommendations": _meta_recommendations(insight_sections),
        "sources": {
            "ui_approval_audits": len(signals.get("audits") or []),
            "operational_memory_records": len(signals.get("memory_records") or []),
            "rollback_journal": len(signals.get("rollbacks") or []),
            "rollout_journal": len(signals.get("rollouts") or []),
            "cross_session_memory": bool(signals.get("cross_session_memory")),
        },
    }
    return GovernanceInsightsResult(
        ok=True,
        session_id=sid,
        insights=payload,
        detail="Meta-governance insights built (read-only).",
    )
