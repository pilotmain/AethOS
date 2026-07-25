# SPDX-License-Identifier: Apache-2.0
"""Environment readiness doctor — PASS / WARNING / FAIL checks."""

from __future__ import annotations

from pathlib import Path
from time import time
from typing import Any, Literal

CheckStatus = Literal["PASS", "WARNING", "FAIL"]

_CHECK = dict[str, Any]


def _check(
    name: str,
    status: CheckStatus,
    *,
    category: str,
    detail: str,
    fix_hint: str | None = None,
    error_code: str | None = None,
) -> _CHECK:
    row: _CHECK = {
        "name": name,
        "status": status,
        "category": category,
        "detail": detail,
        "fix_hint": fix_hint,
    }
    if error_code and status != "PASS":
        from aethos_core.enterprise.actionable_errors import build_actionable_error

        row["actionable"] = build_actionable_error(error_code, detail=detail)
    return row


def run_doctor_checks(
    *,
    probe_api: bool = True,
    probe_web: bool = True,
    probe_browser: bool = False,
    validate_credentials: bool = False,
    category: str | None = None,
) -> dict[str, Any]:
    """Run all environment readiness checks — no secrets in output."""
    checks: list[_CHECK] = []
    checks.extend(_check_api(probe=probe_api))
    checks.extend(_check_web(probe=probe_web))
    checks.extend(_check_telegram())
    checks.extend(_check_tunnel())
    checks.extend(_check_providers(validate=validate_credentials))
    checks.extend(_check_research())
    checks.extend(_check_browser(probe=probe_browser))
    checks.extend(_check_workspace())
    checks.extend(_check_artifacts())
    checks.extend(_check_vault())
    checks.extend(_check_safe_defaults())
    checks.extend(_check_cloud_readonly_inventory())

    if category:
        checks = [c for c in checks if c.get("category") == category]

    counts = {"PASS": 0, "WARNING": 0, "FAIL": 0}
    for c in checks:
        counts[str(c.get("status", "FAIL"))] = counts.get(str(c.get("status")), 0) + 1

    overall: CheckStatus = "PASS"
    if counts["FAIL"] > 0:
        overall = "FAIL"
    elif counts["WARNING"] > 0:
        overall = "WARNING"

    return {
        "ok": overall != "FAIL",
        "overall": overall,
        "checked_at": time(),
        "counts": counts,
        "checks": checks,
        "summary": f"{counts['PASS']} pass · {counts['WARNING']} warning · {counts['FAIL']} fail",
    }


def _check_api(*, probe: bool) -> list[_CHECK]:
    from aethos_core.config import get_settings

    s = get_settings()
    if not probe:
        return [_check("api_config", "PASS", category="api", detail=f"API configured on port {s.api_port}")]
    try:
        import httpx

        url = f"http://127.0.0.1:{s.api_port}/api/v1/health"
        r = httpx.get(url, timeout=3.0)
        if r.status_code == 200:
            return [_check("api_running", "PASS", category="api", detail=f"API healthy at {url}")]
        return [
            _check(
                "api_running",
                "FAIL",
                category="api",
                detail=f"API returned HTTP {r.status_code}",
                fix_hint="./run.sh",
                error_code="api_unreachable",
            )
        ]
    except Exception as exc:
        return [
            _check(
                "api_running",
                "FAIL",
                category="api",
                detail=str(exc)[:120],
                fix_hint="./run.sh",
                error_code="api_unreachable",
            )
        ]


def _check_web(*, probe: bool) -> list[_CHECK]:
    if not probe:
        return [_check("web_ui", "PASS", category="web", detail="Web probe skipped")]
    try:
        import httpx

        r = httpx.get("http://127.0.0.1:3000", timeout=3.0, follow_redirects=True)
        if r.status_code < 500:
            return [_check("web_ui", "PASS", category="web", detail="Web UI reachable at http://localhost:3000")]
        return [
            _check(
                "web_ui",
                "WARNING",
                category="web",
                detail=f"Web UI returned HTTP {r.status_code}",
                fix_hint="cd web && npm run dev",
                error_code="web_unreachable",
            )
        ]
    except Exception:
        return [
            _check(
                "web_ui",
                "WARNING",
                category="web",
                detail="Web UI not reachable (optional for API-only use)",
                fix_hint="cd web && npm run dev",
                error_code="web_unreachable",
            )
        ]


def _check_telegram() -> list[_CHECK]:
    from aethos_core.channels.telegram.telegram_runtime import telegram_channel_status
    from aethos_core.config import get_settings

    s = get_settings()
    if not s.telegram_enabled:
        return [_check("telegram", "PASS", category="telegram", detail="Telegram disabled (safe default)")]
    status = telegram_channel_status(include_webhook=True)
    if status.get("configured") and status.get("transport_health") == "ok":
        wh = status.get("webhook") or {}
        if wh.get("configured"):
            return [_check("telegram_webhook", "PASS", category="telegram", detail="Telegram configured with webhook")]
        return [
            _check(
                "telegram_webhook",
                "WARNING",
                category="telegram",
                detail="Telegram token OK but webhook not configured",
                fix_hint="Configure tunnel or set webhook URL",
                error_code="tunnel_not_configured",
            )
        ]
    return [
        _check(
            "telegram",
            "FAIL" if s.telegram_enabled else "WARNING",
            category="telegram",
            detail="Telegram enabled but token missing or transport degraded",
            fix_hint="Add TELEGRAM_BOT_TOKEN or vault credential",
            error_code="telegram_token_missing",
        )
    ]


def _check_tunnel() -> list[_CHECK]:
    from aethos_core.config import get_settings
    from aethos_core.enterprise.doctor_profile import resolve_doctor_profile

    s = get_settings()
    if not s.telegram_tunnel_enabled:
        return [_check("ngrok_tunnel", "PASS", category="tunnel", detail="Tunnel disabled (safe default)")]
    try:
        from aethos_core.runtime.tunnel.tunnel_manager import tunnel_status

        ts = tunnel_status()
        tunnel = ts.get("tunnel") or {}
        is_running = tunnel.get("status") == "running" or bool(tunnel.get("running"))
        if is_running and tunnel.get("public_url"):
            return [_check("ngrok_tunnel", "PASS", category="tunnel", detail=f"Tunnel active: {tunnel.get('public_url')}")]
        profile = resolve_doctor_profile()
        severity: CheckStatus = "WARNING" if profile in {"development", "staging", "relaxed"} else "FAIL"
        return [
            _check(
                "ngrok_tunnel",
                severity,
                category="tunnel",
                detail="Tunnel enabled but not running",
                fix_hint="aethos tunnel start  (or POST /api/v1/runtime/tunnel/start)",
                error_code="tunnel_not_configured",
            )
        ]
    except Exception as exc:
        return [
            _check(
                "ngrok_tunnel",
                "FAIL",
                category="tunnel",
                detail=str(exc)[:120],
                fix_hint="aethos tunnel start",
                error_code="tunnel_not_configured",
            )
        ]


def _check_providers(*, validate: bool) -> list[_CHECK]:
    from aethos_core.api.provider_readiness import build_provider_readiness

    readiness = build_provider_readiness()
    reqs = readiness.get("requirements") or []
    unmet = [r for r in reqs if not r.get("met")]
    if not unmet:
        return [_check("llm_provider", "PASS", category="providers", detail="LLM provider requirements met")]
    return [
        _check(
            "llm_provider",
            "WARNING",
            category="providers",
            detail=f"{len(unmet)} LLM requirement(s) unmet (optional for deterministic mode)",
            fix_hint="Set USE_REAL_LLM and ANTHROPIC_API_KEY in .env",
        )
    ]


def _check_research() -> list[_CHECK]:
    from aethos_core.config import get_settings
    from aethos_core.research.research_config import build_research_status, research_config_errors

    s = get_settings()
    if not s.web_research_enabled:
        return [_check("research_config", "PASS", category="research", detail="Research disabled (safe default)")]
    errors = research_config_errors(s)
    status = build_research_status(s)
    if errors:
        return [
            _check(
                "research_config",
                "FAIL",
                category="research",
                detail="; ".join(errors[:3]),
                fix_hint="docs/RESEARCH_SETUP.md",
                error_code="research_misconfigured",
            )
        ]
    return [_check("research_config", "PASS", category="research", detail=f"Research configured ({status.get('provider')})")]


def _check_browser(*, probe: bool) -> list[_CHECK]:
    from aethos_core.config import get_settings
    from aethos_core.runtime.browser_capability import get_browser_capability_status

    s = get_settings()
    if not s.browser_automation_enabled:
        return [_check("browser_runtime", "PASS", category="browser", detail="Browser automation disabled (safe default)")]
    cap = get_browser_capability_status(probe_launch=probe)
    if cap.get("execution_ready"):
        return [_check("browser_runtime", "PASS", category="browser", detail="Playwright runtime ready")]
    return [
        _check(
            "browser_runtime",
            "WARNING" if not probe else "FAIL",
            category="browser",
            detail=str(cap.get("execution_label") or cap.get("user_message") or "Not ready")[:120],
            fix_hint="pip install playwright && playwright install chromium",
            error_code="browser_not_ready",
        )
    ]


def _check_workspace() -> list[_CHECK]:
    from aethos_core.runtime.workspace_diagnostics import get_workspace_diagnostics

    ws = get_workspace_diagnostics()
    if ws.get("warning"):
        return [
            _check(
                "workspace_permissions",
                "WARNING",
                category="workspace",
                detail=str(ws["warning"])[:200],
                fix_hint="Set AETHOS_WORKSPACE_ROOT to canonical repo path",
            )
        ]
    return [_check("workspace_permissions", "PASS", category="workspace", detail=f"Workspace: {ws.get('canonical_path')}")]


def _check_artifacts() -> list[_CHECK]:
    from aethos_core.config import get_settings

    s = get_settings()
    dirs = [
        s.agent_artifacts_dir,
        s.browser_artifacts_dir,
        s.research_artifacts_dir,
        s.local_workspace_artifacts_dir,
        "data/presence_memory",
        "data/reliability",
    ]
    missing = []
    for d in dirs:
        p = Path(d)
        if not p.is_dir():
            try:
                p.mkdir(parents=True, exist_ok=True)
            except OSError:
                missing.append(d)
    if missing:
        return [
            _check(
                "artifact_directories",
                "WARNING",
                category="artifacts",
                detail=f"Could not create: {', '.join(missing[:3])}",
                fix_hint="Check disk permissions under data/",
            )
        ]
    return [_check("artifact_directories", "PASS", category="artifacts", detail=f"{len(dirs)} artifact dirs OK")]


def _check_vault() -> list[_CHECK]:
    from aethos_core.security.credential_vault import get_credential_vault_diagnostics

    vault = get_credential_vault_diagnostics()
    if vault.get("available"):
        return [_check("encryption_vault", "PASS", category="vault", detail=f"Vault OK ({vault.get('backend')})")]
    return [
        _check(
            "encryption_vault",
            "FAIL",
            category="vault",
            detail=f"Vault unhealthy: crypto={vault.get('dependencies', {}).get('cryptography')}",
            fix_hint="pip install cryptography",
            error_code="vault_unhealthy",
        )
    ]


def _check_safe_defaults() -> list[_CHECK]:
    from aethos_core.enterprise.doctor_profile import profile_allows_break_glass_warnings, resolve_doctor_profile
    from aethos_core.enterprise.safe_defaults import audit_safe_defaults

    audit = audit_safe_defaults()
    profile = resolve_doctor_profile()
    warnings = list(audit.get("warnings") or [])
    if audit.get("ok") and not warnings:
        return [
            _check(
                "safe_defaults",
                "PASS",
                category="security",
                detail=f"Safe defaults verified (profile={profile})",
            )
        ]
    if audit.get("ok") and warnings and profile_allows_break_glass_warnings():
        return [
            _check(
                "safe_defaults",
                "WARNING",
                category="security",
                detail=f"Break-glass active (profile={profile}): {'; '.join(warnings[:3])}",
                fix_hint="Set AETHOS_OPERATOR_BREAK_GLASS_ACKNOWLEDGED=false and disable HOST_EXECUTOR / production mutations for strict PASS",
            )
        ]
    violations = audit.get("violations") or audit.get("hard_failures") or []
    return [
        _check(
            "safe_defaults",
            "FAIL",
            category="security",
            detail=f"profile={profile}: {'; '.join(violations[:3]) or '; '.join(warnings[:3])}",
            fix_hint="Review .env — see docs/OPERATOR_PRODUCTION_HARDENING_AND_PHASE4_MANUAL_TEST.md",
            error_code="mutation_unsafe",
        )
    ]


def _check_cloud_readonly_inventory() -> list[_CHECK]:
    from aethos_core.config import get_settings

    s = get_settings()
    if not getattr(s, "cloud_readonly_inventory_enabled", False):
        return [
            _check(
                "cloud_readonly_inventory",
                "PASS",
                category="cloud",
                detail="Cloud readonly inventory disabled (safe default)",
            )
        ]
    from aethos_core.providers.cloud.readonly_inventory import list_cloud_readonly_inventory

    snapshot = list_cloud_readonly_inventory(session_id="doctor")
    probes = list(snapshot.get("providers") or [])
    ok_count = sum(1 for row in probes if row.get("ok"))
    partial = [str(row.get("provider")) for row in probes if not row.get("ok")]
    detail = f"Cloud readonly probes: {ok_count}/{len(probes)} ok"
    if partial:
        detail += f" · needs creds/tools: {', '.join(partial[:5])}"
    status: CheckStatus = "PASS" if ok_count else "WARNING"
    return [
        _check(
            "cloud_readonly_inventory",
            status,
            category="cloud",
            detail=detail,
            fix_hint="Configure AWS/GCP/Azure/kubectl/Cloudflare credentials — see Phase 4 manual test doc",
        )
    ]
