# SPDX-License-Identifier: Apache-2.0
"""Continuous Monitor agents — stateful long-horizon watchers.

A Monitor is a persistent, tenant-owned watcher that runs a cheap read-only *probe*
on a schedule, keeps state between runs, and records an observation whenever the
signal changes. This is the "perception" pillar of an agentic OS: AethOS keeps
watching a deploy, an endpoint, a competitor's site, a metric — and remembers.

Design notes
------------
- **Storage**: all monitors live under a single store tenant (``STORE_TENANT``) so the
  scheduler can enumerate every tenant's monitors in one query; each record carries its
  owning ``tenant_id`` and probes run under ``tenant_scope(owner)``. Listing for a user
  filters by owner.
- **Probes** are pluggable (``_PROBES``) and return a small state dict + a one-line
  summary + a change *signature*. A new observation is recorded only when the signature
  changes (or on first run / alert), so the observation log stays signal, not noise.
- **Read-only**: monitors never mutate anything. They observe and remember; surfacing /
  notifying is handled downstream (Daily Digest, Activity feed).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable
from uuid import uuid4

from aethos_core.tenancy import get_current_tenant, tenant_scope
from aethos_core.tenancy.tenant_data_store import (
    delete_record,
    get_record,
    list_records,
    set_record,
)

_log = logging.getLogger("aethos.monitors")

NAMESPACE = "agent_monitors"
# Single storage tenant so run_due_monitors can see every tenant's monitors at once.
STORE_TENANT = "__system__"
MAX_OBSERVATIONS = 50
DEFAULT_INTERVAL_SEC = 300.0
MIN_INTERVAL_SEC = 60.0


def _now() -> float:
    return time.time()


# ───────────────────────────── probes ─────────────────────────────
# Each probe takes the monitor's target string and returns:
#   {"state": {...}, "summary": "<one line>", "signature": "<change key>", "alert": bool}
# `signature` drives change detection; `alert` forces an observation (e.g. site is down).


def _probe_url(target: str) -> dict[str, Any]:
    """Watch an HTTP endpoint / competitor site / status page: up/down, status, latency."""
    import httpx

    url = target.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    started = _now()
    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            resp = client.get(url)
        latency_ms = int((_now() - started) * 1000)
        ok = resp.status_code < 400
        state = {"status_code": resp.status_code, "ok": ok, "latency_ms": latency_ms}
        summary = (
            f"{url} → HTTP {resp.status_code} ({latency_ms}ms)"
            if ok
            else f"⚠ {url} → HTTP {resp.status_code} ({latency_ms}ms)"
        )
        return {"state": state, "summary": summary, "signature": f"{ok}:{resp.status_code}", "alert": not ok}
    except Exception as exc:  # noqa: BLE001 — unreachable is a legitimate observation
        state = {"status_code": None, "ok": False, "error": exc.__class__.__name__}
        return {
            "state": state,
            "summary": f"⚠ {url} unreachable ({exc.__class__.__name__})",
            "signature": f"down:{exc.__class__.__name__}",
            "alert": True,
        }


def _probe_deploy(target: str) -> dict[str, Any]:
    """Watch a deployment's health (restart/failure signals). Target is a free-text hint."""
    try:
        from aethos_core.agents.providers.deployment_intelligence import build_deployment_intelligence

        intel = build_deployment_intelligence(target or "deployment health monitor")
        restarts = int(intel.get("restart_count") or 0)
        provider = str(intel.get("provider") or "railway")
        healthy = restarts < 2
        state = {"restart_count": restarts, "provider": provider, "healthy": healthy}
        summary = (
            f"{provider} deploy healthy (restarts={restarts})"
            if healthy
            else f"⚠ {provider} deploy unstable ({restarts} restart/failure signals)"
        )
        return {"state": state, "summary": summary, "signature": f"{healthy}:{restarts}", "alert": not healthy}
    except Exception as exc:  # noqa: BLE001
        return {
            "state": {"error": exc.__class__.__name__},
            "summary": f"deploy probe error ({exc.__class__.__name__})",
            "signature": "error",
            "alert": False,
        }


_PROBES: dict[str, Callable[[str], dict[str, Any]]] = {
    "url": _probe_url,
    "deploy": _probe_deploy,
}


def monitor_kinds() -> list[dict[str, str]]:
    return [
        {"kind": "url", "label": "Endpoint / website", "hint": "Watch a URL for up/down, status code, latency."},
        {"kind": "deploy", "label": "Deployment health", "hint": "Watch a deploy for restart/failure signals."},
    ]


# ───────────────────────────── CRUD ─────────────────────────────


def create_monitor(
    *,
    name: str,
    kind: str,
    target: str,
    interval_sec: float = DEFAULT_INTERVAL_SEC,
    notify: str = "digest",
    enabled: bool = True,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    if kind not in _PROBES:
        raise ValueError(f"unknown monitor kind: {kind!r}")
    owner = tenant_id or get_current_tenant() or "default"
    monitor_id = f"mon-{uuid4().hex[:12]}"
    record = {
        "monitor_id": monitor_id,
        "tenant_id": owner,
        "name": (name or kind).strip()[:120],
        "kind": kind,
        "target": (target or "").strip()[:500],
        "interval_sec": max(MIN_INTERVAL_SEC, float(interval_sec or DEFAULT_INTERVAL_SEC)),
        "notify": notify if notify in ("digest", "none") else "digest",
        "enabled": bool(enabled),
        "created_at": _now(),
        "last_run_at": None,
        "last_summary": None,
        "state": {},
        "observations": [],
    }
    set_record(NAMESPACE, monitor_id, record, tenant_id=STORE_TENANT)
    return record


def get_monitor(monitor_id: str) -> dict[str, Any] | None:
    rec = get_record(NAMESPACE, monitor_id, tenant_id=STORE_TENANT, default=None)
    return rec if isinstance(rec, dict) else None


def list_monitors(*, tenant_id: str | None = None, include_all: bool = False) -> list[dict[str, Any]]:
    rows = list_records(NAMESPACE, tenant_id=STORE_TENANT, limit=500)
    if include_all:
        return rows
    owner = tenant_id or get_current_tenant() or "default"
    return [r for r in rows if str(r.get("tenant_id")) == owner]


def update_monitor(monitor_id: str, **changes: Any) -> dict[str, Any] | None:
    rec = get_monitor(monitor_id)
    if not rec:
        return None
    for key in ("name", "target", "notify"):
        if key in changes and changes[key] is not None:
            rec[key] = str(changes[key])[:500]
    if "interval_sec" in changes and changes["interval_sec"] is not None:
        rec["interval_sec"] = max(MIN_INTERVAL_SEC, float(changes["interval_sec"]))
    if "enabled" in changes and changes["enabled"] is not None:
        rec["enabled"] = bool(changes["enabled"])
    set_record(NAMESPACE, monitor_id, rec, tenant_id=STORE_TENANT)
    return rec


def delete_monitor(monitor_id: str) -> bool:
    if not get_monitor(monitor_id):
        return False
    return delete_record(NAMESPACE, monitor_id, tenant_id=STORE_TENANT)


def recent_observations(*, tenant_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Flatten the newest observations across a tenant's monitors (for digest / activity)."""
    owner = tenant_id or get_current_tenant() or "default"
    out: list[dict[str, Any]] = []
    for mon in list_monitors(tenant_id=owner):
        for obs in mon.get("observations", []) or []:
            out.append({**obs, "monitor_id": mon.get("monitor_id"), "monitor_name": mon.get("name")})
    out.sort(key=lambda o: float(o.get("at") or 0), reverse=True)
    return out[:limit]


# ───────────────────────────── execution ─────────────────────────────


def run_monitor(monitor: str | dict[str, Any], *, force: bool = False) -> dict[str, Any]:
    """Run one observation cycle. Records an observation only when the signal changes."""
    rec = get_monitor(monitor) if isinstance(monitor, str) else monitor
    if not rec:
        return {"ok": False, "error": "monitor_not_found"}
    kind = str(rec.get("kind"))
    probe = _PROBES.get(kind)
    if not probe:
        return {"ok": False, "error": "unknown_kind", "kind": kind}

    owner = str(rec.get("tenant_id") or "default")
    try:
        with tenant_scope(owner):
            result = probe(str(rec.get("target") or ""))
    except Exception as exc:  # noqa: BLE001 — a probe must never crash the loop
        _log.warning("monitor %s probe failed: %s", rec.get("monitor_id"), exc.__class__.__name__)
        return {"ok": False, "error": "probe_failed", "detail": exc.__class__.__name__}

    new_sig = str(result.get("signature"))
    prev_sig = (rec.get("state") or {}).get("signature")
    changed = prev_sig is None or new_sig != prev_sig or bool(result.get("alert") and prev_sig is None)

    if changed:
        obs = {
            "at": _now(),
            "summary": result.get("summary"),
            "signature": new_sig,
            "alert": bool(result.get("alert")),
        }
        rec["observations"] = ([obs] + (rec.get("observations") or []))[:MAX_OBSERVATIONS]

    rec["state"] = {"signature": new_sig, **(result.get("state") or {})}
    rec["last_run_at"] = _now()
    rec["last_summary"] = result.get("summary")
    set_record(NAMESPACE, str(rec.get("monitor_id")), rec, tenant_id=STORE_TENANT)
    return {
        "ok": True,
        "monitor_id": rec.get("monitor_id"),
        "changed": changed,
        "summary": result.get("summary"),
        "alert": bool(result.get("alert")),
    }


def run_due_monitors(*, force: bool = False) -> dict[str, Any]:
    """Scheduler entry point: run every enabled monitor whose interval has elapsed.

    Runs across all tenants (each under its own scope). Safe to call from the
    observation scheduler; never raises.
    """
    ran: list[dict[str, Any]] = []
    now = _now()
    for rec in list_monitors(include_all=True):
        if not rec.get("enabled"):
            continue
        last = float(rec.get("last_run_at") or 0)
        if not force and (now - last) < float(rec.get("interval_sec") or DEFAULT_INTERVAL_SEC):
            continue
        try:
            ran.append(run_monitor(rec, force=force))
        except Exception as exc:  # noqa: BLE001
            _log.warning("run_due_monitors: %s failed: %s", rec.get("monitor_id"), exc.__class__.__name__)
    return {"ok": True, "ran": len(ran), "results": ran}
