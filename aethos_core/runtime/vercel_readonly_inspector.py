# SPDX-License-Identifier: Apache-2.0
"""Read-only Vercel dashboard inspection — structured inventory, not raw text dumps."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aethos_core.runtime.browser_diagnostics import should_mark_profile_expired_from_error
from aethos_core.runtime.browser_driver import DriverHandle, get_browser_driver
from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import BrowserProfileStatus
from aethos_core.runtime.browser_readiness import preflight_readonly_profile
from aethos_core.browser.platforms.vercel import (
    VercelInventoryArtifact,
    build_chat_summary_bullets,
    build_full_inventory_report,
    build_inventory_artifact,
    build_inventory_from_page,
    build_operational_summary,
)
from aethos_core.runtime.operational_memory import (
    compute_vercel_memory_delta,
    operational_memory,
)
from aethos_core.connections.adapters import auth_method_label

VERCEL_DASHBOARD_URL = "https://vercel.com/dashboard"
TOOL_USED = "vercel_readonly_inspector"
API_TOOL_USED = "vercel_api"


@dataclass
class ReadonlyInspectionOutcome:
    full_result: str
    summary: str
    preview: str
    profile_status: str
    used_saved_session: bool
    profile_id: str
    project_names: list[str]
    inventory: VercelInventoryArtifact | None = None
    operational_summary: str = ""
    debug_excerpt: str | None = None
    login_wall: bool = False


def _extract_visible_text(page: Any, *, max_chars: int = 12_000) -> str:
    try:
        body = page.locator("body").inner_text(timeout=10_000)
    except Exception:
        try:
            body = page.inner_text("body")
        except Exception:
            body = ""
    text = re.sub(r"\n{3,}", "\n\n", (body or "").strip())
    return text[:max_chars]


def _looks_like_login_wall(title: str, url: str, text: str) -> bool:
    low = f"{title} {url} {text[:800]}".lower()
    if "login" in url.lower() or "sign-in" in url.lower() or "signin" in url.lower():
        return True
    markers = ("sign in", "log in", "continue with", "authenticate", "email address")
    return sum(1 for m in markers if m in low) >= 2


def _summary_for_inspection(
    *,
    job_type: str,
    login_wall: bool,
    artifact: VercelInventoryArtifact | None,
    operational_summary: str,
) -> str:
    if login_wall:
        return (
            "Saved Vercel session appears expired or not logged in. "
            "Re-open a supervised session and save again."
        )
    if job_type == "vercel_projects_inventory" and operational_summary:
        return operational_summary
    if artifact and artifact.projects:
        return build_operational_summary(artifact)
    if job_type == "vercel_service_health_summary":
        return "Vercel service health summary (read-only) — see Mission Control."
    return "Vercel deployment status summary (read-only) — see Mission Control."


def _run_inspection_on_browser_thread(
    *,
    job_type: str,
    title: str,
    profile_id: str,
) -> ReadonlyInspectionOutcome:
    profile = preflight_readonly_profile(profile_id)
    storage_path = Path(profile.storage_path)

    browser_profile_store.touch_used(profile.profile_id)
    driver = get_browser_driver()
    handle: DriverHandle | None = None
    try:
        handle = driver.open_url(
            VERCEL_DASHBOARD_URL,
            headless=True,
            storage_state_path=str(storage_path.resolve()),
        )
        page = handle.page
        page_title = ""
        url = VERCEL_DASHBOARD_URL
        try:
            page_title = page.title() or ""
            url = page.url or url
        except Exception:
            pass
        text = _extract_visible_text(page)
        login_wall = _looks_like_login_wall(page_title, url, text)
        if login_wall:
            browser_profile_store.set_status(profile.profile_id, BrowserProfileStatus.EXPIRED)
            artifact = build_inventory_artifact([], extraction_method="login_wall")
            full = build_full_inventory_report(
                title=title,
                job_type=job_type,
                profile_id=profile.profile_id,
                site=profile.site,
                page_title=page_title,
                url=url,
                artifact=artifact,
                login_wall=True,
                auth_method=auth_method_label("browser"),
                browser_used=True,
                provider_used="none",
                masked_credential=f"{profile.profile_id} (session)",
            )
            summary = _summary_for_inspection(
                job_type=job_type,
                login_wall=True,
                artifact=artifact,
                operational_summary="",
            )
            return ReadonlyInspectionOutcome(
                full_result=full,
                summary=summary,
                preview=summary[:240],
                profile_status=profile.status.value,
                used_saved_session=True,
                profile_id=profile.profile_id,
                project_names=[],
                inventory=artifact,
                login_wall=True,
            )

        known_memory = operational_memory.known_vercel_projects()
        memory_context = operational_memory.get_vercel_project_memory()
        artifact, method = build_inventory_from_page(
            page,
            known_projects=known_memory,
            memory_context=memory_context,
            page_url=url,
            page_title=page_title,
            visible_text=text,
            drilldown=job_type == "vercel_projects_inventory",
        )
        from aethos_core.runtime.browser_diagnostics import record_browser_operation_success

        record_browser_operation_success()

        known_before = list(known_memory)
        operational_memory.record_vercel_extraction(
            artifact,
            profile_id=profile.profile_id,
        )
        artifact.memory_delta = compute_vercel_memory_delta(
            [p.name for p in artifact.projects],
            known_before,
        )
        operational_summary = build_operational_summary(artifact)
        chat_bullets = build_chat_summary_bullets(artifact)
        project_names = [p.name for p in artifact.projects]

        full = build_full_inventory_report(
            title=title,
            job_type=job_type,
            profile_id=profile.profile_id,
            site=profile.site,
            page_title=page_title,
            url=url,
            artifact=artifact,
            login_wall=False,
            debug_excerpt=text if job_type == "vercel_projects_inventory" else None,
            known_projects=known_before,
            auth_method=auth_method_label("browser"),
            browser_used=True,
            provider_used="none",
            masked_credential=f"{profile.profile_id} (session)",
        )
        summary = operational_summary if job_type == "vercel_projects_inventory" else chat_bullets

        return ReadonlyInspectionOutcome(
            full_result=full,
            summary=summary,
            preview=operational_summary[:240] if operational_summary else chat_bullets[:240],
            profile_status=profile.status.value,
            used_saved_session=True,
            profile_id=profile.profile_id,
            project_names=project_names,
            inventory=artifact,
            operational_summary=operational_summary,
            debug_excerpt=text[:4000] if text else None,
            login_wall=False,
        )
    finally:
        if handle is not None:
            driver.close_handle(handle)


def run_api_readonly_inspection(
    *,
    job_type: str,
    title: str,
    credential_id: str,
    user_request: str = "",
) -> ReadonlyInspectionOutcome:
    _ = user_request
    from aethos_core.providers.vercel.auth import VercelAuthAdapter
    from aethos_core.providers.vercel.inventory_api import build_api_inventory_report

    cid = (credential_id or "").strip()
    if not cid:
        raise RuntimeError("No Vercel API credential id for read-only inspection.")
    from aethos_core.security.credential_vault import get_credential_vault

    vault = get_credential_vault()
    storage = vault.inspect_secret_storage(cid)
    token = VercelAuthAdapter().get_api_token(cid)
    if not token:
        if not storage.get("has_metadata"):
            raise RuntimeError("Vercel credential not found in the vault for this tenant.")
        if storage.get("failure_class") == "encrypted_secret_missing" or not storage.get(
            "has_encrypted_secret"
        ):
            raise RuntimeError(
                "Vercel API token is not available in this runtime — the credential vault "
                "is not synced across processes. Re-save the token in Mission Control → Advanced settings → Credentials "
                "and ensure DATABASE_URL and AETHOS_VAULT_KEY match on api and worker."
            )
        if storage.get("failure_class") == "decrypt_failed":
            raise RuntimeError(
                "Vercel API token could not be decrypted — set the same AETHOS_VAULT_KEY on "
                "every api/worker service."
            )
        raise RuntimeError(
            f"Vercel API token unavailable ({storage.get('failure_class') or 'vault_read_failed'})."
        )
    artifact, operational_summary, full = build_api_inventory_report(
        token,
        title=title,
        job_type=job_type,
        credential_id=cid,
    )
    from aethos_core.runtime.operational_memory import compute_vercel_memory_delta

    known_before = operational_memory.known_vercel_projects()
    operational_memory.record_vercel_extraction(artifact, profile_id=cid)
    artifact.memory_delta = compute_vercel_memory_delta(
        [p.name for p in artifact.projects],
        known_before,
    )
    chat_bullets = build_chat_summary_bullets(artifact)
    summary = operational_summary if job_type == "vercel_projects_inventory" else chat_bullets
    return ReadonlyInspectionOutcome(
        full_result=full,
        summary=summary,
        preview=(operational_summary or chat_bullets)[:240],
        profile_status="api_token",
        used_saved_session=False,
        profile_id=cid,
        project_names=[p.name for p in artifact.projects],
        inventory=artifact,
        operational_summary=operational_summary,
        login_wall=False,
    )


def run_vercel_readonly_inspection(
    *,
    job_type: str,
    title: str,
    user_request: str = "",
    auth_method: str = "browser",
    profile_id: str = "",
    credential_id: str = "",
) -> ReadonlyInspectionOutcome:
    if auth_method == "api_token":
        return run_api_readonly_inspection(
            job_type=job_type,
            title=title,
            credential_id=credential_id,
            user_request=user_request,
        )
    return run_readonly_inspection(
        job_type=job_type,
        title=title,
        profile_id=profile_id,
        user_request=user_request,
    )


def run_readonly_inspection(
    *,
    job_type: str,
    title: str,
    profile_id: str,
    user_request: str = "",
) -> ReadonlyInspectionOutcome:
    from aethos_core.runtime.browser_runtime import run_browser_sync

    pid = (profile_id or "").strip()
    if not pid:
        raise RuntimeError("No saved browser profile id for read-only inspection.")

    return run_browser_sync(
        lambda: _run_inspection_on_browser_thread(
            job_type=job_type,
            title=title,
            profile_id=pid,
        ),
        timeout=120.0,
    )


def run_profile_session_check(profile_id: str) -> dict[str, Any]:
    profile = browser_profile_store.get(profile_id)
    if not profile:
        raise KeyError(profile_id)
    try:
        outcome = run_readonly_inspection(
            job_type="vercel_projects_inventory",
            title="Profile session test",
            profile_id=profile_id,
        )
        login_wall = outcome.login_wall
        if login_wall:
            browser_profile_store.set_status(profile.profile_id, BrowserProfileStatus.EXPIRED)
        else:
            browser_profile_store.set_status(profile.profile_id, BrowserProfileStatus.ACTIVE)
        return {
            "profile_id": profile_id,
            "ok": not login_wall,
            "status": browser_profile_store.get(profile_id).status.value,
            "message": outcome.operational_summary or outcome.summary,
            "project_count": len(outcome.project_names),
        }
    except Exception as exc:
        from aethos_core.runtime.browser_diagnostics import (
            BrowserRuntimeNotReady,
            classify_playwright_error,
            is_browser_runtime_error,
            runtime_not_ready_message,
        )

        status = profile.status
        runtime_status = "failed"
        inspection_status = "not_run"
        message = str(exc)
        if is_browser_runtime_error(exc):
            kind = classify_playwright_error(message)
            if kind == "asyncio_sync_api_misuse":
                message = (
                    "Browser runtime bug: Playwright Sync API was called inside the asyncio loop. "
                    "This is an AethOS runtime issue, not a Chromium install issue."
                )
            elif isinstance(exc, BrowserRuntimeNotReady):
                try:
                    from aethos_core.runtime.browser_diagnostics import probe_playwright_on_browser_thread

                    message = runtime_not_ready_message(probe_playwright_on_browser_thread())
                except Exception:
                    pass
        elif should_mark_profile_expired_from_error(exc):
            browser_profile_store.set_status(profile.profile_id, BrowserProfileStatus.EXPIRED)
            status = BrowserProfileStatus.EXPIRED
            inspection_status = "session_invalid"
        return {
            "profile_id": profile_id,
            "ok": False,
            "status": status.value,
            "profile_status": status.value,
            "runtime_status": runtime_status,
            "inspection_status": inspection_status,
            "message": message,
        }


def export_storage_from_session_handle(handle: DriverHandle) -> dict[str, Any]:
    driver = get_browser_driver()
    return driver.export_storage_state(handle)
