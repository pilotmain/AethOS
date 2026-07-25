# SPDX-License-Identifier: Apache-2.0
"""Skill optimization from traces — improve playbooks from real run history.

Records lightweight per-skill traces (outcome + detail) as skills are used, then turns
that history into an **optimization proposal**: how often the skill succeeded/failed and
the recurring failure patterns, with suggested "Lessons learned" bullets to add. It is
strictly read-only with respect to the skill files — it proposes, the operator applies.

Deterministic by default (counts + recurring substrings); set ``SKILL_OPTIMIZATION_LLM``
to polish the suggestions into prose.
"""

from __future__ import annotations

import re
import time
from collections import Counter
from typing import Any

from aethos_core.tenancy import get_current_tenant
from aethos_core.tenancy.tenant_data_store import get_record, set_record

TRACE_NAMESPACE = "skill_traces"
MAX_TRACES = 200


def _now() -> float:
    return time.time()


def record_skill_trace(
    skill_id: str, *, outcome: str, detail: str = "", tenant_id: str | None = None
) -> dict[str, Any]:
    """Append a usage trace for a skill. ``outcome`` is e.g. 'success' / 'failure'."""
    owner = tenant_id or get_current_tenant() or "default"
    key = (skill_id or "").strip()
    if not key:
        return {"ok": False, "error": "skill_id_required"}
    rec = get_record(TRACE_NAMESPACE, key, tenant_id=owner, default=None) or {"skill_id": key, "traces": []}
    rec["traces"] = (
        [{"at": _now(), "outcome": (outcome or "unknown").strip().lower(), "detail": (detail or "")[:300]}]
        + (rec.get("traces") or [])
    )[:MAX_TRACES]
    set_record(TRACE_NAMESPACE, key, rec, tenant_id=owner)
    return {"ok": True, "skill_id": key, "trace_count": len(rec["traces"])}


def list_skill_traces(skill_id: str, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
    owner = tenant_id or get_current_tenant() or "default"
    rec = get_record(TRACE_NAMESPACE, (skill_id or "").strip(), tenant_id=owner, default=None) or {}
    return list(rec.get("traces") or [])


def _load_skills() -> list[dict[str, Any]]:
    try:
        from aethos_core.operational_skill_runtime.skill_loader import load_local_operator_skills

        return list(load_local_operator_skills().get("skills") or [])
    except Exception:
        return []


def skills_with_trace_counts(*, tenant_id: str | None = None) -> list[dict[str, Any]]:
    out = []
    for sk in _load_skills():
        traces = list_skill_traces(str(sk.get("id")), tenant_id=tenant_id)
        failures = sum(1 for t in traces if t.get("outcome") == "failure")
        out.append(
            {
                "id": sk.get("id"),
                "name": sk.get("name"),
                "description": sk.get("description"),
                "trace_count": len(traces),
                "failure_count": failures,
            }
        )
    return out


_WORD_RX = re.compile(r"[a-z0-9]{4,}")
_STOP = frozenset("with from this that error failed when after before unable could would should".split())


def _failure_patterns(traces: list[dict[str, Any]], *, top: int = 3) -> list[dict[str, Any]]:
    """Most common salient terms across failure details — the recurring trouble spots."""
    counter: Counter[str] = Counter()
    for t in traces:
        if t.get("outcome") != "failure":
            continue
        for w in _WORD_RX.findall(str(t.get("detail") or "").lower()):
            if w not in _STOP:
                counter[w] += 1
    return [{"term": term, "count": n} for term, n in counter.most_common(top) if n >= 2]


def propose_skill_optimization(
    skill_id: str, *, tenant_id: str | None = None, use_llm: bool | None = None
) -> dict[str, Any]:
    """Build an improvement proposal for a skill from its traces. Read-only — never edits."""
    key = (skill_id or "").strip()
    skill = next((s for s in _load_skills() if str(s.get("id")) == key), None)
    if not skill:
        return {"ok": False, "error": "skill_not_found", "skill_id": key}

    traces = list_skill_traces(key, tenant_id=tenant_id)
    total = len(traces)
    failures = [t for t in traces if t.get("outcome") == "failure"]
    success = sum(1 for t in traces if t.get("outcome") == "success")
    patterns = _failure_patterns(traces)

    if total == 0:
        summary = f"No traces yet for '{skill.get('name')}'. Use it a few times to gather signal."
        suggestions: list[str] = []
    else:
        rate = round(100 * success / total) if total else 0
        summary = f"{skill.get('name')}: {total} runs, {success} ok, {len(failures)} failed ({rate}% success)."
        suggestions = [f"Add guidance for the recurring issue: '{p['term']}' ({p['count']}×)." for p in patterns]
        if failures and not patterns:
            suggestions.append("Failures lack a common term — capture richer failure detail in traces.")
        if rate >= 90 and total >= 5:
            suggestions.append("High success rate — consider promoting this skill / tightening its trigger.")

    want_llm = False
    if use_llm is None:
        from aethos_core.config import get_settings

        want_llm = bool(getattr(get_settings(), "skill_optimization_llm", False))
    else:
        want_llm = use_llm

    if want_llm and suggestions:
        try:
            from aethos_core.provider.completion import complete_chat, provider_configured

            if provider_configured():
                ctx = f"Skill: {skill.get('name')}\nDescription: {skill.get('description')}\nSignals:\n" + "\n".join(
                    f"- {s}" for s in suggestions
                )
                overlay = "Turn these signals into 2-4 concrete, actionable edits to the skill playbook. Be specific."
                res = complete_chat(ctx, include_identity=False, system_overlay=overlay)
                if (res.text or "").strip():
                    suggestions = [ln.strip("-• ").strip() for ln in res.text.splitlines() if ln.strip()][:6]
        except Exception:  # noqa: BLE001
            pass

    return {
        "ok": True,
        "skill_id": key,
        "name": skill.get("name"),
        "summary": summary,
        "trace_count": total,
        "failure_count": len(failures),
        "failure_patterns": patterns,
        "suggestions": suggestions,
    }
