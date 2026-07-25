# SPDX-License-Identifier: Apache-2.0
"""Supervised browser phase — extract Supabase API settings after operator login."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from time import sleep, time
from typing import Any

from aethos_core.provider_e2e_orchestration.env_completion.supabase_constants import (
    SUPABASE_API_SETTINGS_URL,
    SUPABASE_ENV_VAR_NAMES,
)
from aethos_core.security.secret_redaction import redact_text

_SUPABASE_URL_RX = re.compile(r"https://[a-z0-9-]+\.supabase\.co", re.I)
_JWT_RX = re.compile(r"\beyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b")
_LOGIN_WALL_RX = re.compile(r"\b(sign in|log in|continue with github|magic link)\b", re.I)


@dataclass
class SupabaseBrowserExtractionResult:
    ok: bool
    values: dict[str, str] = field(default_factory=dict)
    detail: str = ""
    login_wall: bool = False
    session_id: str = ""
    errors: list[str] = field(default_factory=list)


def run_supabase_browser_extraction(
    *,
    chat_session_id: str = "default",
    timeout_sec: float = 120.0,
    poll_interval_sec: float = 2.0,
) -> SupabaseBrowserExtractionResult:
    """Open supervised Supabase API settings; operator logs in; extract URL + anon key."""
    from aethos_core.config import get_settings
    from aethos_core.runtime.browser_capability import get_browser_capability_status
    from aethos_core.runtime.browser_session import browser_session_store

    settings = get_settings()
    if not settings.browser_automation_enabled:
        return SupabaseBrowserExtractionResult(
            ok=False,
            detail="Browser automation is disabled — add values via Connections or enable BROWSER_AUTOMATION_ENABLED.",
        )

    status = get_browser_capability_status(probe_launch=False)
    if not status.get("enabled"):
        return SupabaseBrowserExtractionResult(
            ok=False,
            detail=str(status.get("detail") or "Browser runtime not ready."),
        )

    session = browser_session_store.start_supervised_session(
        target=SUPABASE_API_SETTINGS_URL,
        chat_session_id=chat_session_id,
        login_notice=True,
    )
    deadline = time() + max(10.0, timeout_sec)
    last_detail = "Waiting for Supabase login and API settings page…"

    try:
        while time() < deadline:
            live = browser_session_store.get(session.id)
            if live is None:
                return SupabaseBrowserExtractionResult(
                    ok=False,
                    session_id=session.id,
                    detail="Browser session ended before extraction.",
                )
            if live.status.value in {"failed", "closed", "cancelled"}:
                return SupabaseBrowserExtractionResult(
                    ok=False,
                    session_id=session.id,
                    detail=redact_text(str(live.error or "Browser session failed.")),
                )

            page_text = _read_active_page_text(session.id)
            if page_text:
                if _LOGIN_WALL_RX.search(page_text) and "project url" not in page_text.lower():
                    last_detail = "Login required — complete sign-in in the browser window."
                else:
                    extracted = _extract_supabase_values(page_text)
                    if extracted.get(SUPABASE_ENV_VAR_NAMES[0]) and extracted.get(SUPABASE_ENV_VAR_NAMES[1]):
                        return SupabaseBrowserExtractionResult(
                            ok=True,
                            values=extracted,
                            session_id=session.id,
                            detail="Extracted Supabase Project URL and anon key from API settings (values not logged).",
                        )
            sleep(poll_interval_sec)

        return SupabaseBrowserExtractionResult(
            ok=False,
            session_id=session.id,
            login_wall=True,
            detail=last_detail,
            errors=["Timed out waiting for Supabase API settings after login."],
        )
    finally:
        try:
            browser_session_store.close(session.id)
        except Exception:
            pass


def _read_active_page_text(session_id: str) -> str:
    from aethos_core.runtime.browser_runtime import run_browser_sync

    def _read() -> str:
        from aethos_core.runtime.browser_session import browser_session_store

        session = browser_session_store.get(session_id)
        if session is None or session._handle is None or session._handle.page is None:
            return ""
        page = session._handle.page
        try:
            body = page.inner_text("body", timeout=3000)
        except Exception:
            body = ""
        try:
            inputs = page.eval_on_selector_all(
                "input",
                "els => els.map(e => e.value || e.getAttribute('value') || '')",
            )
        except Exception:
            inputs = []
        chunks = [str(body or "")]
        chunks.extend(str(v) for v in (inputs or []) if str(v).strip())
        return "\n".join(chunks)

    try:
        return str(run_browser_sync(_read, timeout=15.0) or "")
    except Exception:
        return ""


def _extract_supabase_values(page_text: str) -> dict[str, str]:
    text = str(page_text or "")
    values: dict[str, str] = {}
    url_match = _SUPABASE_URL_RX.search(text)
    if url_match:
        values[SUPABASE_ENV_VAR_NAMES[0]] = url_match.group(0).rstrip("/")
    jwt_matches = _JWT_RX.findall(text)
    if jwt_matches:
        values[SUPABASE_ENV_VAR_NAMES[1]] = jwt_matches[0]
    return values


def resolve_supabase_env_via_management(
    *,
    params: dict[str, Any],
    requested_names: list[str],
) -> tuple[dict[str, str], dict[str, Any]]:
    """Resolve Supabase env values from the account-wide Management API PAT.

    Selects or (when requested) creates a project, then fetches its URL + keys on
    demand. The service_role key is only fetched when SUPABASE_SERVICE_ROLE_KEY is
    requested and is treated as vault-only (never logged). All values flow into the
    same governed env-completion gate; this only resolves values, it does not apply
    them. Returns ({} , trace) when no PAT / flag off / no resolvable project.
    """
    import secrets as _secrets

    from aethos_core.providers.supabase import management_adapter as mgmt

    trace: dict[str, Any] = {"attempted": True}
    if not mgmt.management_enabled():
        trace.update({"ok": False, "reason": "provisioning_disabled"})
        return {}, trace
    if not mgmt.has_management_token():
        trace.update({"ok": False, "reason": "no_management_token"})
        return {}, trace

    ref = str(params.get("supabase_project_ref") or params.get("project_ref") or "").strip()
    create_req = params.get("supabase_create_project")

    # Create a new project (governed: the job only runs after MC approval).
    if not ref and isinstance(create_req, dict) and create_req.get("name") and create_req.get("organization_id"):
        created = mgmt.create_project(
            name=str(create_req.get("name")),
            organization_id=str(create_req.get("organization_id")),
            region=str(create_req.get("region") or "us-east-1"),
            db_pass=str(create_req.get("db_pass") or _secrets.token_urlsafe(24)),
            plan=str(create_req.get("plan") or "free"),
        )
        if not created.get("ok"):
            trace.update({"ok": False, "reason": "create_failed", "detail": created.get("detail")})
            return {}, trace
        ref = str(created.get("ref") or "")
        trace["created_project"] = {"ref": ref, "name": created.get("name")}

    # Otherwise select: explicit ref, else the only visible project.
    if not ref:
        listing = mgmt.list_projects()
        if not listing.get("ok"):
            trace.update({"ok": False, "reason": listing.get("error") or "list_failed"})
            return {}, trace
        projects = listing.get("projects") or []
        trace["visible_project_count"] = len(projects)
        if len(projects) == 1:
            ref = str(projects[0].get("ref") or "")
            trace["auto_selected_ref"] = ref
        else:
            trace.update({"ok": False, "reason": "project_not_selected"})
            return {}, trace

    keys = mgmt.get_project_keys(ref)
    if not keys.get("ok"):
        trace.update({"ok": False, "reason": keys.get("error") or "keys_failed", "ref": ref})
        return {}, trace

    requested = {str(n).strip().upper() for n in requested_names}
    values: dict[str, str] = {}
    if keys.get("url"):
        values["NEXT_PUBLIC_SUPABASE_URL"] = str(keys["url"])
    if keys.get("anon_key"):
        values["NEXT_PUBLIC_SUPABASE_ANON_KEY"] = str(keys["anon_key"])
    if "SUPABASE_SERVICE_ROLE_KEY" in requested and keys.get("service_role_key"):
        values["SUPABASE_SERVICE_ROLE_KEY"] = str(keys["service_role_key"])

    trace.update(
        {
            "ok": True,
            "ref": ref,
            # Names only — never the secret values.
            "resolved_names": sorted(values.keys()),
            "service_role_resolved": "SUPABASE_SERVICE_ROLE_KEY" in values,
        }
    )
    return values, trace


def collect_supabase_values_from_sources(
    *,
    plan: dict[str, Any],
    params: dict[str, Any],
    chat_session_id: str = "default",
) -> tuple[dict[str, str], dict[str, Any]]:
    """Resolve Supabase env values: submitted params → browser → solo local env."""
    collected: dict[str, str] = {}
    trace: dict[str, Any] = {"sources": []}

    submitted = params.get("submitted_env_values")
    if isinstance(submitted, dict):
        for name, value in submitted.items():
            cleaned = str(value or "").strip()
            if cleaned:
                collected[str(name).strip().upper()] = cleaned
        if collected:
            trace["sources"].append("submitted_params")

    # Management API source — one account-wide PAT resolves a project's URL + keys
    # on demand (no manual key entry). Runs after explicitly submitted values so an
    # operator-selected project/value always wins (§5 backward compatibility).
    requested_names = list(params.get("missing_env_names") or SUPABASE_ENV_VAR_NAMES)
    if any(n not in collected for n in requested_names):
        mgmt_values, mgmt_trace = resolve_supabase_env_via_management(
            params=params,
            requested_names=requested_names,
        )
        trace["management"] = mgmt_trace
        if mgmt_values:
            for name, value in mgmt_values.items():
                if value and name not in collected:
                    collected[name.upper()] = value
            trace["sources"].append("management_api")

    missing = [n for n in SUPABASE_ENV_VAR_NAMES if n not in collected]
    if missing and params.get("browser_extraction_enabled", True):
        from aethos_core.governance.approval_privacy_governance import browser_capture_requires_approval

        if browser_capture_requires_approval() and not params.get("browser_capture_approved"):
            trace["browser"] = {
                "ok": False,
                "detail": "Browser capture requires Mission Control approval when BROWSER_CAPTURE_APPROVAL_REQUIRED=true.",
                "blocked": True,
            }
        else:
            browser = run_supabase_browser_extraction(chat_session_id=chat_session_id)
            trace["browser"] = {
                "ok": browser.ok,
                "detail": browser.detail,
                "login_wall": browser.login_wall,
                "session_id": browser.session_id,
            }
            if browser.ok:
                for name, value in browser.values.items():
                    if value and name not in collected:
                        collected[name.upper()] = value
                trace["sources"].append("browser_extraction")

    missing = [n for n in SUPABASE_ENV_VAR_NAMES if n not in collected]
    if missing:
        from aethos_core.providers.railway.env_value_readiness.env_value_inventory import _local_trusted_secret_value

        for name in missing:
            local = _local_trusted_secret_value(name)
            if local:
                collected[name] = local
        if any(n in collected for n in missing):
            trace["sources"].append("local_env_dev_only")

    return collected, trace
