# SPDX-License-Identifier: Apache-2.0
"""Operational health dashboard — unified system health rollup."""

from __future__ import annotations

from time import time
from typing import Any


def build_operational_health_dashboard() -> dict[str, Any]:
    """Aggregate health for Mission Control dashboard."""
    from aethos_core.enterprise.demo_mode import demo_status, get_demo_overlay
    from aethos_core.enterprise.doctor import run_doctor_checks
    from aethos_core.runtime.authority import authority

    doctor = run_doctor_checks(probe_api=False, probe_web=False, probe_browser=False)
    auth = authority.snapshot()

    scheduler = _scheduler_health()
    queue = _queue_health()
    providers = _provider_auth_health()
    tunnel = _tunnel_health()
    browser = _browser_health()
    artifacts = _artifact_health()
    reliability = _reliability_score()

    components = {
        "api": _component_from_doctor(doctor, "api"),
        "scheduler": scheduler,
        "queue": queue,
        "providers": providers,
        "tunnel": tunnel,
        "browser": browser,
        "artifacts": artifacts,
        "reliability": reliability,
    }

    unhealthy = sum(1 for c in components.values() if c.get("status") == "FAIL")
    degraded = sum(1 for c in components.values() if c.get("status") == "WARNING")

    overall = "healthy"
    if unhealthy:
        overall = "unhealthy"
    elif degraded:
        overall = "degraded"

    return {
        "ok": overall != "unhealthy",
        "overall": overall,
        "checked_at": time(),
        "authority": auth,
        "doctor_summary": doctor.get("summary"),
        "doctor_overall": doctor.get("overall"),
        "components": components,
        "demo": demo_status(),
        "demo_overlay": get_demo_overlay() if demo_status().get("enabled") else None,
        "readonly": True,
    }


def _component_from_doctor(doctor: dict[str, Any], category: str) -> dict[str, Any]:
    checks = [c for c in doctor.get("checks") or [] if c.get("category") == category]
    if not checks:
        return {"status": "PASS", "detail": "No checks"}
    worst = "PASS"
    for c in checks:
        st = str(c.get("status"))
        if st == "FAIL":
            worst = "FAIL"
            break
        if st == "WARNING" and worst == "PASS":
            worst = "WARNING"
    return {"status": worst, "checks": checks}


def _scheduler_health() -> dict[str, Any]:
    try:
        from aethos_core.runtime.schedulers.observation_scheduler import scheduler_status

        st = scheduler_status()
        running = st.get("running")
        errors = int((st.get("stats") or {}).get("errors") or 0)
        status = "PASS" if running and errors == 0 else "WARNING" if running else "FAIL"
        return {"status": status, "running": running, "errors": errors, "schedules": st.get("schedules")}
    except Exception as exc:
        return {"status": "WARNING", "detail": str(exc)[:80]}


def _queue_health() -> dict[str, Any]:
    try:
        from aethos_core.channels.telegram.telegram_delivery import queue_snapshot

        q = queue_snapshot()
        pending = int(q.get("pending") or q.get("queue_depth") or 0)
        status = "PASS" if pending < 10 else "WARNING"
        return {"status": status, "pending": pending}
    except Exception:
        return {"status": "PASS", "detail": "Queue metrics unavailable"}


def _provider_auth_health() -> dict[str, Any]:
    try:
        from aethos_core.connections.credential_hydration import build_credential_center_payload

        center = build_credential_center_payload()
        creds = center.get("credentials") or []
        invalid = sum(1 for c in creds if c.get("validation_status") == "invalid")
        status = "PASS" if invalid == 0 else "WARNING" if invalid < 3 else "FAIL"
        return {"status": status, "credential_count": len(creds), "invalid_count": invalid}
    except Exception:
        return {"status": "PASS", "detail": "Provider inventory optional"}


def _tunnel_health() -> dict[str, Any]:
    from aethos_core.config import get_settings

    if not get_settings().telegram_tunnel_enabled:
        return {"status": "PASS", "detail": "Tunnel disabled"}
    try:
        from aethos_core.runtime.tunnel.tunnel_manager import tunnel_status

        ts = tunnel_status()
        status = "PASS" if ts.get("running") else "FAIL"
        return {"status": status, "running": ts.get("running"), "public_url": ts.get("public_url")}
    except Exception as exc:
        return {"status": "FAIL", "detail": str(exc)[:80]}


def _browser_health() -> dict[str, Any]:
    from aethos_core.config import get_settings

    if not get_settings().browser_automation_enabled:
        return {"status": "PASS", "detail": "Browser disabled"}
    try:
        from aethos_core.runtime.browser_capability import get_browser_capability_status

        cap = get_browser_capability_status(probe_launch=False)
        status = "PASS" if cap.get("execution_ready") else "WARNING"
        return {"status": status, "execution_ready": cap.get("execution_ready"), "label": cap.get("execution_label")}
    except Exception as exc:
        return {"status": "WARNING", "detail": str(exc)[:80]}


def _artifact_health() -> dict[str, Any]:
    from pathlib import Path

    from aethos_core.config import get_settings

    s = get_settings()
    dirs = [s.agent_artifacts_dir, s.browser_artifacts_dir, s.research_artifacts_dir]
    ok = all(Path(d).is_dir() for d in dirs)
    return {"status": "PASS" if ok else "WARNING", "directories_checked": len(dirs)}


def _reliability_score() -> dict[str, Any]:
    try:
        from aethos_core.reliability.reliability_runtime import assess_operational_reliability

        rel = assess_operational_reliability()
        scores = rel.get("scores") or {}
        return {
            "status": "PASS" if float(scores.get("global_reliability_score") or 0) >= 0.5 else "WARNING",
            "global_score": scores.get("global_reliability_score"),
            "trust_level": scores.get("trust_level"),
            "truth_state": (rel.get("reliability") or {}).get("truth_state"),
        }
    except Exception:
        return {"status": "PASS", "detail": "Reliability module optional"}
