# SPDX-License-Identifier: Apache-2.0
"""Daily Digest agent — a scheduled morning briefing.

Gathers signals that already exist across AethOS (deploy health, jobs, pending
approvals, monitor observations, connected social) into a single briefing, stores the
latest, and optionally pushes it to Telegram. Composition is **deterministic by default**
(no token cost — respects BYOK economics); set ``DIGEST_LLM=true`` to polish into prose.

Each signal is gathered defensively (try/except → a graceful line) so one failing
subsystem never breaks the digest.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

from aethos_core.config import get_settings
from aethos_core.tenancy import get_current_tenant, tenant_scope
from aethos_core.tenancy.tenant_data_store import get_record, set_record

_log = logging.getLogger("aethos.digest")

NAMESPACE = "daily_digest"


def _now() -> float:
    return time.time()


def _section(title: str, lines: list[str]) -> dict[str, Any]:
    return {"title": title, "lines": lines}


# ───────────────────────────── signal gatherers ─────────────────────────────


def _deploy_section() -> dict[str, Any]:
    try:
        from aethos_core.agents.providers.deployment_intelligence import build_deployment_intelligence

        intel = build_deployment_intelligence("daily digest deployment health")
        restarts = int(intel.get("restart_count") or 0)
        provider = str(intel.get("provider") or "railway")
        if restarts >= 2:
            return _section("Deployments", [f"⚠ {provider}: {restarts} restart/failure signals — check it."])
        return _section("Deployments", [f"{provider}: healthy (restarts={restarts})."])
    except Exception:
        return _section("Deployments", ["(deployment health unavailable)"])


def _jobs_section() -> dict[str, Any]:
    try:
        from aethos_core.jobs.job_state import list_jobs

        jobs = list_jobs(limit=100)
        active = [j for j in jobs if j.get("status") in {"queued", "running", "scheduled", "retrying"}]
        failed = [j for j in jobs if j.get("status") in {"failed", "error"}]
        lines = [f"{len(active)} active, {len(failed)} failed (recent)."]
        for j in failed[:3]:
            lines.append(f"⚠ failed: {str(j.get('title') or j.get('kind') or j.get('job_id'))[:60]}")
        return _section("Jobs", lines)
    except Exception:
        return _section("Jobs", ["(jobs unavailable)"])


def _approvals_section() -> dict[str, Any]:
    try:
        from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload

        inbox = approval_inbox_payload(session_id="digest")
        pending = inbox.get("summary", {}).get("total_pending")
        if pending is None:
            pending = len(inbox.get("pending") or inbox.get("items") or [])
        return _section("Approvals", [f"{pending} pending approval(s)." if pending else "Nothing waiting on you."])
    except Exception:
        return _section("Approvals", ["(approvals unavailable)"])


def _monitors_section() -> dict[str, Any]:
    try:
        from aethos_core.monitors import recent_observations

        obs = recent_observations(limit=8)
        if not obs:
            return _section("Monitors", ["No recent changes."])
        lines = []
        for o in obs[:6]:
            mark = "⚠ " if o.get("alert") else ""
            lines.append(f"{mark}{o.get('monitor_name')}: {o.get('summary')}")
        return _section("Monitors", lines)
    except Exception:
        return _section("Monitors", ["(monitors unavailable)"])


def _social_section() -> dict[str, Any]:
    try:
        from aethos_core.social.connectors import connected_platforms

        connected = connected_platforms()
        return _section(
            "Social",
            [f"Connected: {', '.join(connected)}." if connected else "No social platforms connected."],
        )
    except Exception:
        return _section("Social", ["(social unavailable)"])


def _render_text(sections: list[dict[str, Any]], *, when: datetime) -> str:
    out = [f"☀️ AethOS Daily Digest — {when.strftime('%A %d %b %Y, %H:%M')}", ""]
    for sec in sections:
        out.append(f"**{sec['title']}**")
        for line in sec["lines"]:
            out.append(f"  • {line}")
        out.append("")
    return "\n".join(out).strip()


def _llm_polish(text: str) -> str:
    try:
        from aethos_core.provider.completion import complete_chat, provider_configured

        if not provider_configured():
            return text
        overlay = (
            "Rewrite this operations digest as a crisp, friendly morning briefing for the operator. "
            "Keep every fact and warning; be concise; no preamble."
        )
        result = complete_chat(text, include_identity=False, system_overlay=overlay)
        return (result.text or "").strip() or text
    except Exception:
        return text


# ───────────────────────────── build / deliver ─────────────────────────────


def build_digest(*, tenant_id: str | None = None, use_llm: bool | None = None) -> dict[str, Any]:
    """Assemble the digest for a tenant. Read-only; safe to call any time."""
    owner = tenant_id or get_current_tenant() or "default"

    def _safe(fn, title: str) -> dict[str, Any]:
        try:
            return fn()
        except Exception:  # noqa: BLE001 — one bad signal must never break the digest
            return _section(title, [f"({title.lower()} unavailable)"])

    with tenant_scope(owner):
        sections = [
            _safe(_deploy_section, "Deployments"),
            _safe(_jobs_section, "Jobs"),
            _safe(_approvals_section, "Approvals"),
            _safe(_monitors_section, "Monitors"),
            _safe(_social_section, "Social"),
        ]
    when = datetime.now()
    text = _render_text(sections, when=when)
    settings = get_settings()
    want_llm = settings.digest_llm if use_llm is None else use_llm
    if want_llm:
        text = _llm_polish(text)
    return {"generated_at": _now(), "tenant_id": owner, "sections": sections, "text": text}


def deliver_digest(*, tenant_id: str | None = None) -> dict[str, Any]:
    """Build, persist as 'latest', emit an operational event, and push to Telegram if set."""
    owner = tenant_id or get_current_tenant() or "default"
    digest = build_digest(tenant_id=owner)
    set_record(NAMESPACE, "latest", digest, tenant_id=owner)
    set_record(NAMESPACE, "_last_delivered_date", {"date": datetime.now().strftime("%Y-%m-%d")}, tenant_id=owner)

    delivered_to = ["stored"]
    try:
        from aethos_core.agents.memory.operational_patterns import record_operational_event

        record_operational_event(category="daily_digest", detail="Daily digest generated", provider="aethos")
        delivered_to.append("activity_feed")
    except Exception:
        pass

    chat_id = str(get_settings().digest_telegram_chat or "").strip()
    if chat_id:
        try:
            from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token
            from aethos_core.channels.telegram.telegram_transport import send_telegram_message

            with tenant_scope(owner):
                token, _ = resolve_telegram_bot_token()
            if token:
                res = send_telegram_message(token=token, chat_id=chat_id, text=digest["text"])
                if res.get("ok"):
                    delivered_to.append("telegram")
        except Exception as exc:  # noqa: BLE001
            _log.warning("digest telegram push failed: %s", exc.__class__.__name__)

    return {"ok": True, "delivered_to": delivered_to, "digest": digest}


def latest_digest(*, tenant_id: str | None = None) -> dict[str, Any] | None:
    owner = tenant_id or get_current_tenant() or "default"
    rec = get_record(NAMESPACE, "latest", tenant_id=owner, default=None)
    return rec if isinstance(rec, dict) else None


def run_due_digests(*, force: bool = False) -> dict[str, Any]:
    """Scheduler entry (hourly tick). Delivers once per day at the configured hour.

    Runs for the operator/default tenant. ``force`` ignores the hour/once-per-day gate.
    """
    settings = get_settings()
    if not force and not settings.digest_enabled:
        return {"ok": True, "delivered": False, "reason": "disabled"}
    owner = get_current_tenant() or "default"
    now = datetime.now()
    if not force:
        if now.hour != int(settings.digest_hour or 8):
            return {"ok": True, "delivered": False, "reason": "not_digest_hour"}
        last = get_record(NAMESPACE, "_last_delivered_date", tenant_id=owner, default={}) or {}
        if last.get("date") == now.strftime("%Y-%m-%d"):
            return {"ok": True, "delivered": False, "reason": "already_delivered_today"}
    result = deliver_digest(tenant_id=owner)
    return {"ok": True, "delivered": True, "delivered_to": result["delivered_to"]}
