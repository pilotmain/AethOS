# SPDX-License-Identifier: Apache-2.0
"""KERNEL_REALITY_PROOF_001 — persistent operational evidence from live kernel turns."""

from __future__ import annotations

import json
import re
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

OutcomeKind = Literal["success", "failure", "recovery", "no_match"]
SourceChannel = Literal["chat", "cli", "operational"]
ProofCategory = Literal["inventory", "logs", "deployments", "health", "followups", "continue", "other"]

_CONTINUITY_PROMPTS = (
    r"\btop \d+ only\b",
    r"\bwhat about\b",
    r"\bshow logs\b",
    r"\bcan you give me that\b",
    r"\bgive me that\b",
    r"\bthat (one|deployment|service)\b",
    r"\bresume\b",
    r"\bsame (service|thing)\b",
)

_RAILWAY_RX = re.compile(r"\brailway\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)

_lock = threading.Lock()
_memory_records: list[dict[str, Any]] = []


@dataclass
class KernelRealityRecord:
    record_id: str
    timestamp: str
    provider: str
    session_id: str
    request: str
    subject: str
    goal: str
    outcome: OutcomeKind
    recovery_used: bool
    fallback_used: bool
    source: SourceChannel = "chat"
    category: ProofCategory = "other"
    operation: str = ""
    intent: str = ""
    ok: bool = True
    provider_confusion: bool = False
    continuity_prompt: bool = False
    continuity_retained: bool | None = None
    requested_provider: str = ""
    resolved_provider: str = ""
    correct_provider: bool = True
    routing_confidence: str = ""
    provider_misroute: bool = False
    manual_correction_required: bool = False
    meta: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _store_dir() -> Path:
    from aethos_core.config import get_settings

    root = Path(get_settings().agent_artifacts_dir).parent / "operational_kernel_reality"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _records_path() -> Path:
    return _store_dir() / "records.jsonl"


def _daily_path() -> Path:
    return _store_dir() / "daily_snapshots.json"


def reality_capture_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(get_settings().kernel_reality_capture_enabled)


def classify_proof_category(*, operation: str, intent: str, request: str) -> ProofCategory:
    op = (operation or "").lower()
    intent_lower = (intent or "").lower()
    if op in {"list_inventory", "list_services"} or "list_inventory" in intent_lower:
        return "inventory"
    if op == "fetch_logs" or "fetch_logs" in intent_lower:
        return "logs"
    if op in {"deployment_status", "list_deployments"} or "deployment_status" in intent_lower:
        return "deployments"
    if op == "health_check" or "health_check" in intent_lower:
        return "health"
    if "continue_plan" in intent or "deploy_plan" in intent:
        return "continue"
    if is_continuity_prompt(request):
        return "followups"
    if "continue" in (request or "").lower():
        return "continue"
    return "other"


def is_continuity_prompt(text: str) -> bool:
    raw = (text or "").strip()
    return any(re.search(rx, raw, re.I) for rx in _CONTINUITY_PROMPTS)


def detect_provider_confusion(*, request: str, provider: str, subject_label: str) -> bool:
    raw = (request or "").lower()
    prov = (provider or "").lower()
    subj = (subject_label or "").lower()
    wants_vercel = bool(_VERCEL_RX.search(raw)) or "killit" in raw
    wants_railway = bool(_RAILWAY_RX.search(raw)) or "aethos-api" in raw or "aethos-ui" in raw
    if wants_vercel and prov == "railway" and not wants_railway:
        return True
    if wants_railway and prov == "vercel" and not wants_vercel:
        return True
    if wants_vercel and "aethos-api" in subj and "killit" not in subj:
        return True
    if "killit" in raw and prov == "railway":
        return True
    return False


def _subject_label(subject: Any) -> str:
    if subject is None:
        return ""
    if isinstance(subject, str):
        return subject
    if isinstance(subject, dict):
        parts = [
            subject.get("provider"),
            subject.get("vercel_project") or subject.get("project"),
            subject.get("alias"),
        ]
        return " / ".join(str(p) for p in parts if p)
    provider = getattr(subject, "provider", "") or ""
    project = getattr(subject, "vercel_project", "") or getattr(subject, "project", "") or ""
    alias = getattr(subject, "alias", "") or ""
    return " / ".join(str(p) for p in (provider, project or alias) if p)


def _evaluate_continuity(*, session_id: str, request: str, subject_label: str) -> bool | None:
    if not is_continuity_prompt(request):
        return None
    try:
        from aethos_core.operational_session.operational_session import load_operational_session

        session = load_operational_session(session_id=session_id)
        if not session.has_active_subject():
            return False
        prior = _subject_label(session.subject)
        if not prior:
            return None
        if "what about" in request.lower() and subject_label:
            return True
        if subject_label and prior.split("/")[0].strip().lower() == subject_label.split("/")[0].strip().lower():
            return True
        return bool(subject_label)
    except Exception:
        return None


def append_kernel_reality_record(record: KernelRealityRecord) -> None:
    payload = record.to_dict()
    with _lock:
        _memory_records.append(payload)
        if reality_capture_enabled():
            with _records_path().open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def capture_kernel_reality_turn(
    *,
    request: str,
    session_id: str,
    source: SourceChannel,
    ok: bool,
    intent: str,
    meta: dict[str, str] | None = None,
    subject: Any = None,
    prior_subject: Any = None,
) -> KernelRealityRecord | None:
    if not reality_capture_enabled():
        return None

    meta = dict(meta or {})
    provider = str(meta.get("readonly_provider") or meta.get("provider") or "").lower()
    if not provider and subject is not None:
        provider = str(getattr(subject, "provider", "") or "").lower()
    operation = str(meta.get("operation") or meta.get("last_operation") or "")
    goal_kind = str(meta.get("goal_kind") or "")
    goal = goal_kind or operation or intent

    recovery_used = meta.get("recovery_applied") == "true" or "recovery" in intent
    fallback_used = meta.get("kernel_fallback") == "true" or meta.get("kernel_no_match") == "true"

    if meta.get("kernel_no_match") == "true" or intent == "operational_kernel_no_match":
        outcome: OutcomeKind = "no_match"
    elif recovery_used and ok:
        outcome = "recovery"
    elif ok:
        outcome = "success"
    elif recovery_used:
        outcome = "recovery"
    else:
        outcome = "failure"

    subject_label = _subject_label(subject)
    category = classify_proof_category(operation=operation, intent=intent, request=request)
    continuity = _evaluate_continuity(session_id=session_id, request=request, subject_label=subject_label)
    from aethos_core.operational_session.provider_routing_proof import evaluate_provider_routing

    routing = evaluate_provider_routing(request=request, resolved_provider=provider)
    confusion = routing.provider_misroute or detect_provider_confusion(
        request=request, provider=provider, subject_label=subject_label
    )

    record = KernelRealityRecord(
        record_id=str(uuid.uuid4()),
        timestamp=datetime.now(UTC).isoformat(),
        provider=provider or "unknown",
        session_id=session_id,
        request=(request or "")[:500],
        subject=subject_label[:240],
        goal=goal[:120],
        outcome=outcome,
        recovery_used=recovery_used,
        fallback_used=fallback_used,
        source=source,
        category=category,
        operation=operation,
        intent=intent,
        ok=ok,
        provider_confusion=confusion,
        continuity_prompt=is_continuity_prompt(request),
        continuity_retained=continuity,
        requested_provider=routing.requested_provider,
        resolved_provider=routing.resolved_provider,
        correct_provider=routing.correct_provider,
        routing_confidence=routing.confidence,
        provider_misroute=routing.provider_misroute,
        manual_correction_required=routing.manual_correction_required,
        meta={k: str(v) for k, v in meta.items() if k not in {"reply"}},
    )
    append_kernel_reality_record(record)
    _increment_live_metrics(record)
    from aethos_core.operational_session.user_friction_registry import record_friction_event

    record_friction_event(
        session_id=session_id,
        request=request,
        ok=ok,
        intent=intent,
        fallback_used=fallback_used,
        provider_misroute=routing.provider_misroute,
        manual_correction=routing.manual_correction_required,
    )
    return record


def _increment_live_metrics(record: KernelRealityRecord) -> None:
    from aethos_core.observability.metrics import increment

    increment("kernel_turns")
    if record.ok and record.outcome in {"success", "recovery"}:
        increment("successful_turns")
    if not record.ok and record.outcome == "failure":
        increment("failed_turns")
    if record.recovery_used:
        increment("recovered_turns")
    if record.fallback_used:
        increment("fallback_turns")
    if record.outcome == "no_match":
        increment("kernel_no_match_turns")
    if record.provider_confusion or record.provider_misroute:
        increment("provider_confusion_events")
    if record.provider_misroute:
        increment("provider_misroute_count")
    if not record.correct_provider and record.requested_provider:
        increment("provider_correction_rate")
    if record.continuity_prompt:
        increment("conversation_resume_events")
        if record.continuity_retained is False:
            increment("subject_resolution_failures")
    if record.intent == "operational_kernel_needs_target":
        increment("subject_resolution_failures")


def load_reality_records(*, limit: int = 5000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    path = _records_path()
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rid = str(row.get("record_id") or "")
                if rid and rid in seen:
                    continue
                if rid:
                    seen.add(rid)
                rows.append(row)
    with _lock:
        for row in _memory_records:
            rid = str(row.get("record_id") or "")
            if rid and rid in seen:
                continue
            if rid:
                seen.add(rid)
            rows.append(row)
    if limit and len(rows) > limit:
        return rows[-limit:]
    return rows


def _day_key(ts: str) -> str:
    return (ts or "")[:10] or datetime.now(UTC).strftime("%Y-%m-%d")


def compute_reality_summary(*, days: int = 7) -> dict[str, Any]:
    from aethos_core.operational_session.goal_completion_registry import goal_completion_summary
    from aethos_core.operational_session.user_friction_registry import friction_summary

    records = load_reality_records()
    if not records:
        return _empty_summary()

    by_day: dict[str, list[dict]] = {}
    for row in records:
        by_day.setdefault(_day_key(str(row.get("timestamp") or "")), []).append(row)

    day_keys = sorted(by_day.keys())[-days:]
    scoped = [row for key in day_keys for row in by_day[key]]

    total = len(scoped)
    successful = sum(1 for r in scoped if r.get("ok") and r.get("outcome") in {"success", "recovery"})
    failed = sum(1 for r in scoped if r.get("outcome") == "failure")
    recovered = sum(1 for r in scoped if r.get("recovery_used"))
    fallback = sum(1 for r in scoped if r.get("fallback_used"))
    confusion = sum(1 for r in scoped if r.get("provider_confusion"))
    continuity_prompts = [r for r in scoped if r.get("continuity_prompt")]
    continuity_ok = sum(1 for r in continuity_prompts if r.get("continuity_retained") is True)
    continuity_fail = sum(1 for r in continuity_prompts if r.get("continuity_retained") is False)
    recovery_attempts = sum(
        1 for r in scoped if r.get("recovery_used") or r.get("outcome") == "recovery"
    )
    recovery_success = sum(1 for r in scoped if r.get("recovery_used"))

    provider_stats = _provider_proof_stats(scoped)
    failures = _top_failures(scoped)
    regressions = _top_regressions(scoped)
    fallback_rate = round(fallback / total, 4) if total else None

    acceptance = _acceptance_gate(
        provider_stats,
        successful,
        total,
        continuity_ok,
        len(continuity_prompts),
        recovery_success,
        recovery_attempts,
        confusion,
        fallback_rate,
        provider_routing_summary(scoped),
        goal_completion_summary(days=days),
        friction_summary(days=days),
    )

    return {
        "period_days": days,
        "evidence_store": str(_store_dir().resolve()),
        "day_keys": day_keys,
        "total_turns": total,
        "successful_turns": successful,
        "failed_turns": failed,
        "recovered_turns": recovered,
        "fallback_turns": fallback,
        "provider_confusion_events": confusion,
        "conversation_resume_events": len(continuity_prompts),
        "success_rate": round(successful / total, 4) if total else None,
        "recovery_success_rate": round(recovery_success / recovery_attempts, 4) if recovery_attempts else None,
        "fallback_rate": fallback_rate,
        "continuity_accuracy": round(continuity_ok / len(continuity_prompts), 4) if continuity_prompts else None,
        "provider_accuracy": round(1.0 - (confusion / total), 4) if total else None,
        "provider_proof": provider_stats,
        "provider_routing": provider_routing_summary(scoped),
        "goal_completion": goal_completion_summary(days=days),
        "user_friction": friction_summary(days=days),
        "success_report": _format_success_report(
            scoped,
            provider_stats,
            provider_routing_summary(scoped),
            goal_completion_summary(days=days),
            friction_summary(days=days),
            continuity_ok,
            len(continuity_prompts),
            recovery_success,
            recovery_attempts,
            fallback_rate,
        ),
        "acceptance": acceptance,
        "top_failures": failures,
        "top_regressions": regressions,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _empty_summary() -> dict[str, Any]:
    from aethos_core.operational_session.goal_completion_registry import goal_completion_summary
    from aethos_core.operational_session.user_friction_registry import friction_summary

    goals = goal_completion_summary()
    friction = friction_summary()
    routing = provider_routing_summary([])
    acceptance = _acceptance_gate({}, 0, 0, 0, 0, 0, 0, 0, None, routing, goals, friction)
    return {
        "period_days": 7,
        "evidence_store": str(_store_dir().resolve()),
        "day_keys": [],
        "total_turns": 0,
        "successful_turns": 0,
        "failed_turns": 0,
        "recovered_turns": 0,
        "fallback_turns": 0,
        "recovery_success_rate": None,
        "message": "No kernel reality records yet. Use chat or `aethos operational` with capture enabled.",
        "goal_completion": goals,
        "user_friction": friction,
        "provider_routing": routing,
        "success_report": _format_success_report([], {}, routing, goals, friction, 0, 0, 0, 0, None),
        "top_failures": [],
        "top_regressions": [],
        "acceptance": acceptance,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _provider_proof_stats(records: list[dict]) -> dict[str, Any]:
    stats: dict[str, Any] = {}
    for provider in ("railway", "vercel"):
        rows = [r for r in records if str(r.get("provider") or "").lower() == provider]
        ok_rows = [r for r in rows if r.get("ok")]
        by_cat: dict[str, int] = {}
        for r in ok_rows:
            cat = str(r.get("category") or "other")
            by_cat[cat] = by_cat.get(cat, 0) + 1
        stats[provider] = {
            "successful_turns": len(ok_rows),
            "total_turns": len(rows),
            "by_category": by_cat,
            "meets_100_successful": len(ok_rows) >= 100,
            "required_categories": {
                **{
                    cat: by_cat.get(cat, 0) >= 1
                    for cat in ("inventory", "logs", "deployments", "health")
                },
                "followups": (
                    by_cat.get("followups", 0) >= 1
                    or sum(1 for r in ok_rows if r.get("continuity_prompt")) >= 1
                ),
            },
        }
    return stats


def provider_routing_summary(records: list[dict]) -> dict[str, Any]:
    routed = [r for r in records if r.get("requested_provider")]
    if not routed:
        return {
            "provider_accuracy_rate": None,
            "provider_misroute_count": sum(1 for r in records if r.get("provider_misroute")),
            "provider_correction_rate": None,
            "railway_accuracy": None,
            "vercel_accuracy": None,
        }
    correct = sum(1 for r in routed if r.get("correct_provider"))
    misroutes = sum(1 for r in routed if r.get("provider_misroute"))
    total = len(routed)
    by_provider: dict[str, dict[str, int]] = {}
    for row in routed:
        req = str(row.get("requested_provider") or "")
        if req not in {"railway", "vercel"}:
            continue
        bucket = by_provider.setdefault(req, {"total": 0, "correct": 0})
        bucket["total"] += 1
        if row.get("correct_provider"):
            bucket["correct"] += 1
    return {
        "provider_accuracy_rate": round(correct / total, 4) if total else None,
        "provider_misroute_count": misroutes,
        "provider_correction_rate": round(misroutes / total, 4) if total else None,
        "railway_accuracy": round(by_provider.get("railway", {}).get("correct", 0) / by_provider["railway"]["total"], 4)
        if by_provider.get("railway", {}).get("total")
        else None,
        "vercel_accuracy": round(by_provider.get("vercel", {}).get("correct", 0) / by_provider["vercel"]["total"], 4)
        if by_provider.get("vercel", {}).get("total")
        else None,
    }


def _format_success_report(
    records: list[dict],
    provider_stats: dict[str, Any],
    routing: dict[str, Any],
    goals: dict[str, Any],
    friction: dict[str, Any],
    continuity_ok: int,
    continuity_total: int,
    recovery_success: int,
    recovery_attempts: int,
    fallback_rate: float | None,
) -> dict[str, Any]:
    total = len(records)
    soak_pass = False
    return {
        "kernel_turns": total,
        "railway_accuracy_pct": _pct(routing.get("railway_accuracy")),
        "vercel_accuracy_pct": _pct(routing.get("vercel_accuracy")),
        "conversation_continuity_pct": _pct(continuity_ok / continuity_total if continuity_total else None),
        "recovery_success_rate_pct": _pct(recovery_success / recovery_attempts if recovery_attempts else None),
        "provider_misroutes": routing.get("provider_misroute_count", 0),
        "fallback_rate_pct": _pct(fallback_rate),
        "operational_goals_started": goals.get("goals_started", 0),
        "operational_goals_completed": goals.get("goals_completed", 0),
        "goal_completion_rate_pct": _pct(goals.get("goal_completion_rate")),
        "user_retry_count": friction.get("retry_count", 0),
        "user_clarifications": friction.get("clarification_count", 0),
        "seven_day_soak": "PASS" if soak_pass else "PENDING",
    }


def _pct(value: float | None) -> str | float:
    if value is None:
        return "—"
    return round(float(value) * 100, 1)


def _acceptance_gate(
    provider_stats: dict[str, Any],
    successful: int,
    total: int,
    continuity_ok: int,
    continuity_total: int,
    recovery_success: int,
    recovery_attempts: int,
    confusion: int,
    fallback_rate: float | None,
    routing: dict[str, Any],
    goals: dict[str, Any],
    friction: dict[str, Any],
) -> dict[str, Any]:
    railway_ok = (provider_stats.get("railway") or {}).get("successful_turns", 0) >= 100
    vercel_ok = (provider_stats.get("vercel") or {}).get("successful_turns", 0) >= 100
    continuity_rate = continuity_ok / continuity_total if continuity_total else None
    recovery_rate = recovery_success / recovery_attempts if recovery_attempts else None
    routing_accuracy = routing.get("provider_accuracy_rate")
    provider_accuracy = routing_accuracy if routing_accuracy is not None else (1.0 - (confusion / total) if total else None)
    goals_ok = goals.get("meets_20_completed", False)
    friction_ok = friction.get("declining_friction") or friction.get("friction_trend") in {"declining", "stable", "insufficient_data"}
    gates = {
        "railway_100_successful_turns": railway_ok,
        "vercel_100_successful_turns": vercel_ok,
        "continuity_95_percent": continuity_rate is not None and continuity_rate >= 0.95,
        "recovery_90_percent": recovery_rate is not None and recovery_rate >= 0.90,
        "provider_accuracy_95_percent": provider_accuracy is not None and provider_accuracy >= 0.95,
        "fallback_under_5_percent": fallback_rate is None or fallback_rate < 0.05,
        "twenty_goals_completed": goals_ok,
        "friction_declining_or_stable": friction_ok,
        "seven_day_soak_complete": False,
    }
    gates["operationally_proven"] = all(
        [
            gates["railway_100_successful_turns"],
            gates["vercel_100_successful_turns"],
            gates["continuity_95_percent"],
            gates["recovery_90_percent"],
            gates["provider_accuracy_95_percent"],
            gates["fallback_under_5_percent"],
            gates["twenty_goals_completed"],
            gates["seven_day_soak_complete"],
        ]
    )
    gates["ready_for_approval_privacy_rehardening"] = gates["operationally_proven"]
    gates["ready_for_manual_test"] = gates["operationally_proven"]
    return gates


def _top_failures(records: list[dict], *, limit: int = 5) -> list[dict[str, Any]]:
    fails = [r for r in records if r.get("outcome") == "failure" or not r.get("ok")]
    buckets: dict[str, int] = {}
    for row in fails:
        key = str(row.get("intent") or row.get("operation") or "unknown")
        buckets[key] = buckets.get(key, 0) + 1
    return [{"intent": k, "count": v} for k, v in sorted(buckets.items(), key=lambda x: -x[1])[:limit]]


def _top_regressions(records: list[dict], *, limit: int = 5) -> list[dict[str, Any]]:
    reg = [r for r in records if r.get("provider_confusion") or r.get("continuity_retained") is False]
    buckets: dict[str, int] = {}
    for row in reg:
        key = str(row.get("request") or "")[:80]
        buckets[key] = buckets.get(key, 0) + 1
    return [{"request": k, "count": v} for k, v in sorted(buckets.items(), key=lambda x: -x[1])[:limit]]


def _evidence_root() -> Path:
    return _store_dir().parent.parent / "evidence"


def archive_evidence_store(*, day: str | None = None) -> Path | None:
    """Copy the live registry store to evidence/backup-YYYY-MM-DD (repo-root absolute)."""
    import shutil

    store = _store_dir()
    if not store.exists() or not any(store.iterdir()):
        return None
    stamp = day or datetime.now(UTC).strftime("%Y-%m-%d")
    evidence_root = _evidence_root()
    evidence_root.mkdir(parents=True, exist_ok=True)
    backup = evidence_root / f"backup-{stamp}"
    if backup.exists():
        shutil.rmtree(backup)
    shutil.copytree(store, backup)
    return backup


def restore_evidence_backup(*, day: str | None = None) -> dict[str, Any]:
    """Restore registry files from evidence/backup-YYYY-MM-DD into the live store."""
    import shutil

    evidence_root = _evidence_root()
    if not evidence_root.exists():
        return {"ok": False, "error": "No evidence backups found.", "path": str(evidence_root)}

    if day:
        candidates = [evidence_root / f"backup-{day}"]
    else:
        candidates = sorted(
            (p for p in evidence_root.glob("backup-*") if p.is_dir()),
            key=lambda p: p.name,
            reverse=True,
        )

    for backup in candidates:
        records = backup / "records.jsonl"
        if not records.exists():
            continue
        store = _store_dir()
        store.mkdir(parents=True, exist_ok=True)
        restored_count = 0
        for name in ("records.jsonl", "daily_snapshots.json", "goals.jsonl", "friction_events.jsonl"):
            src = backup / name
            if src.exists():
                shutil.copy2(src, store / name)
                if name == "records.jsonl":
                    restored_count = sum(1 for line in src.read_text(encoding="utf-8").splitlines() if line.strip())
        with _lock:
            _memory_records.clear()
            if (store / "records.jsonl").exists():
                with (store / "records.jsonl").open(encoding="utf-8") as handle:
                    for line in handle:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            _memory_records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        return {
            "ok": True,
            "restored_from": str(backup),
            "record_count": restored_count or len(_memory_records),
        }

    return {"ok": False, "error": "No backup with records.jsonl found.", "path": str(evidence_root)}


def save_daily_snapshot(summary: dict[str, Any] | None = None, *, as_date: str | None = None) -> dict[str, Any]:
    summary = summary or compute_reality_summary(days=1)
    if as_date:
        from aethos_core.config import get_settings

        if not bool(get_settings().kernel_soak_dev_accelerate):
            raise ValueError(
                "Synthetic soak dates require KERNEL_SOAK_DEV_ACCELERATE=true (staging/dev only)."
            )
        day = str(as_date).strip()
    else:
        day = datetime.now(UTC).strftime("%Y-%m-%d")
    path = _daily_path()
    existing: dict[str, Any] = {}
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}

    prior = existing.get(day) or {}
    prior_turns = int(((prior.get("summary") or {}).get("total_turns") or 0))
    new_turns = int(summary.get("total_turns") or 0)
    if prior_turns > 0 and new_turns == 0:
        kept = dict(prior)
        kept_summary = dict(kept.get("summary") or {})
        kept_summary["restore_warning"] = (
            "Refused to overwrite non-empty daily snapshot with empty evidence. "
            "Restore from evidence backup or re-run operational turns."
        )
        kept["summary"] = kept_summary
        return kept

    payload = {"date": day, "summary": summary}
    existing[day] = payload
    with _lock:
        path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    return payload


def soak_progress(*, required_days: int = 7) -> dict[str, Any]:
    path = _daily_path()
    if not path.exists():
        return {"days_recorded": 0, "required_days": required_days, "complete": False, "dates": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = {}
    dates = sorted(data.keys())
    recent = dates[-required_days:]
    complete = len(recent) >= required_days and all(
        (data.get(d) or {}).get("summary", {}).get("successful_turns", 0) > 0 for d in recent[-required_days:]
    )
    return {
        "days_recorded": len(dates),
        "required_days": required_days,
        "dates": dates,
        "recent_window": recent,
        "complete": complete,
    }


def clear_reality_registry_for_tests() -> None:
    from aethos_core.operational_session.goal_completion_registry import clear_goal_registry_for_tests
    from aethos_core.operational_session.user_friction_registry import clear_friction_registry_for_tests

    with _lock:
        _memory_records.clear()
    for path in (_records_path(), _daily_path()):
        if path.exists():
            path.unlink()
    clear_goal_registry_for_tests()
    clear_friction_registry_for_tests()
