# SPDX-License-Identifier: Apache-2.0
"""Proactive suggestions — surface "you might want to…" from existing signals.

AethOS scans signals it already collects (monitor alerts, recurring failures, pending
approvals, deploy instability, failing skills) and proposes next actions. This is the
"don't just wait to be asked" pillar — but strictly **governance-gated**: suggestions are
read-only proposals with an action hint; nothing is ever auto-executed. The operator acts.

Off by default (``PROACTIVE_SUGGESTIONS_ENABLED``). Deterministic; no token cost. Dismissed
suggestions are remembered (per tenant) so they don't nag.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from aethos_core.config import get_settings
from aethos_core.tenancy import get_current_tenant, tenant_scope
from aethos_core.tenancy.tenant_data_store import get_record, set_record

NAMESPACE = "proactive"
_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _now() -> float:
    return time.time()


def _sid(source: str, key: str) -> str:
    return "sg-" + hashlib.sha1(f"{source}:{key}".encode()).hexdigest()[:12]


def _suggest(source: str, key: str, title: str, detail: str, severity: str, action_hint: str) -> dict[str, Any]:
    return {
        "id": _sid(source, key),
        "source": source,
        "title": title,
        "detail": detail,
        "severity": severity if severity in _SEVERITY_RANK else "low",
        "action_hint": action_hint,
        "at": _now(),
    }


# ───────────────────────────── signal scanners ─────────────────────────────


def _from_monitors() -> list[dict[str, Any]]:
    try:
        from aethos_core.monitors import recent_observations

        out = []
        for o in recent_observations(limit=10):
            if o.get("alert"):
                out.append(
                    _suggest(
                        "monitor",
                        str(o.get("monitor_id")),
                        f"Investigate monitor: {o.get('monitor_name')}",
                        str(o.get("summary") or ""),
                        "high",
                        "Open Mission Control → Monitors and review this watcher.",
                    )
                )
        return out
    except Exception:
        return []


def _from_failures() -> list[dict[str, Any]]:
    try:
        from aethos_core.intelligence.operational_memory import recurring_failure_kinds

        out = []
        for f in recurring_failure_kinds(min_count=3, window_hours=48):
            kind = str(f.get("kind") or f.get("category") or "failure")
            out.append(
                _suggest(
                    "failure",
                    kind,
                    f"Recurring failure: {kind}",
                    f"Seen {f.get('count')} times recently.",
                    "medium",
                    "Add a guard/skill for this failure mode.",
                )
            )
        return out
    except Exception:
        return []


def _from_approvals() -> list[dict[str, Any]]:
    try:
        from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload

        inbox = approval_inbox_payload(session_id="proactive")
        pending = inbox.get("summary", {}).get("total_pending")
        if pending is None:
            pending = len(inbox.get("pending") or inbox.get("items") or [])
        if pending:
            return [
                _suggest(
                    "approvals",
                    "pending",
                    f"{pending} approval(s) waiting on you",
                    "Governed actions are paused pending your approval.",
                    "high" if int(pending) >= 3 else "medium",
                    "Open Mission Control → Approvals.",
                )
            ]
        return []
    except Exception:
        return []


def _from_skills() -> list[dict[str, Any]]:
    try:
        from aethos_core.skills import skills_with_trace_counts

        out = []
        for s in skills_with_trace_counts():
            if int(s.get("failure_count") or 0) >= 3:
                out.append(
                    _suggest(
                        "skill",
                        str(s.get("id")),
                        f"Skill failing: {s.get('name')}",
                        f"{s.get('failure_count')} failures recorded.",
                        "medium",
                        "Run skill optimization to propose fixes.",
                    )
                )
        return out
    except Exception:
        return []


def _dismissed(owner: str) -> set[str]:
    rec = get_record(NAMESPACE, "_dismissed", tenant_id=owner, default={}) or {}
    return set(rec.get("ids") or [])


def generate_suggestions(*, tenant_id: str | None = None) -> list[dict[str, Any]]:
    """Scan signals → ranked, de-duplicated, non-dismissed suggestions. [] when disabled."""
    if not getattr(get_settings(), "proactive_suggestions_enabled", False):
        return []
    owner = tenant_id or get_current_tenant() or "default"
    with tenant_scope(owner):
        raw = _from_monitors() + _from_failures() + _from_approvals() + _from_skills()
    dismissed = _dismissed(owner)
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for s in raw:
        if s["id"] in dismissed or s["id"] in seen:
            continue
        seen.add(s["id"])
        out.append(s)
    out.sort(key=lambda s: (_SEVERITY_RANK.get(s["severity"], 2), -s["at"]))
    return out


def run_proactive_scan(*, tenant_id: str | None = None) -> dict[str, Any]:
    """Generate + persist the latest suggestion set (scheduler/manual entry)."""
    owner = tenant_id or get_current_tenant() or "default"
    suggestions = generate_suggestions(tenant_id=owner)
    set_record(NAMESPACE, "latest", {"at": _now(), "suggestions": suggestions}, tenant_id=owner)
    return {"ok": True, "count": len(suggestions), "suggestions": suggestions}


def latest_suggestions(*, tenant_id: str | None = None) -> list[dict[str, Any]]:
    owner = tenant_id or get_current_tenant() or "default"
    # Always regenerate live so dismissals/new signals reflect immediately.
    return generate_suggestions(tenant_id=owner)


def dismiss_suggestion(suggestion_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
    owner = tenant_id or get_current_tenant() or "default"
    rec = get_record(NAMESPACE, "_dismissed", tenant_id=owner, default={}) or {}
    ids = set(rec.get("ids") or [])
    ids.add((suggestion_id or "").strip())
    set_record(NAMESPACE, "_dismissed", {"ids": sorted(ids)}, tenant_id=owner)
    return {"ok": True, "dismissed": suggestion_id}
