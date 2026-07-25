# SPDX-License-Identifier: Apache-2.0
"""FastAPI entry — chat-first, no MC coupling."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from aethos_core.config import get_settings

_log = logging.getLogger(__name__)

_LOCAL_DEV_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
)

_deferred_bootstrap_complete = False


def _cors_allowed_origins() -> list[str]:
    """Credentialed browser calls cannot use ``Access-Control-Allow-Origin: *``.

    Local dev (UI :3000, API :8010) needs explicit origins so session cookies stick.
    """
    settings = get_settings()
    origins = [o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()]
    if settings.app_env in {"development", "local", "dev"} or settings.deployment_mode == "local":
        origins.extend(_LOCAL_DEV_CORS_ORIGINS)
    if not origins:
        origins.extend(
            [
                "https://pilotmain.com",
                "https://www.pilotmain.com",
            ]
        )
    return list(dict.fromkeys(origins))


def _mount_core_routes(app: FastAPI) -> None:
    """Light routers for first paint — health, auth, chat, onboarding, providers."""
    from aethos_core.api.routes import aethos_identity, chat, health, providers, pwa, tenant_onboarding

    app.include_router(health.router, prefix="/api/v1")
    app.include_router(aethos_identity.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(tenant_onboarding.router, prefix="/api/v1")
    app.include_router(providers.router, prefix="/api/v1")
    app.include_router(pwa.router, prefix="/api/v1")


def _mount_deferred_routes(app: FastAPI) -> None:
    """Remaining routers — lazy import so cold boot can answer /health immediately."""
    from aethos_core.api.routes import (
        actions,
        agents,
        arbiter,
        automation,
        autonomous_execution,
        browser,
        catalog,
        digest as digest_routes,
        memory as memory_routes,
        monitors as monitors_routes,
        proactive as proactive_routes,
        skills_optimization as skills_optimization_routes,
        channels,
        connections,
        credentials,
        cross_provider_correlation,
        delivery,
        deployment_targets,
        engineering,
        enterprise,
        external_execution,
        governance_diagnostics,
        human,
        intelligence,
        job_truth,
        jobs,
        legacy,
        mission_control,
        mission_control_live,
        model_selection,
        mutations,
        observability,
        operational_truth,
        orgs,
        plugins,
        presence,
        production,
        provider_topology,
        railway_discovery,
        railway_execution,
        reliability,
        research,
        runtime,
        runtime_config,
        settings,
        slack,
        telegram,
        telegram_soak,
        validation_harness,
        workspace,
        workspaces,
    )

    app.include_router(delivery.router, prefix="/api/v1")
    app.include_router(runtime.router, prefix="/api/v1")
    app.include_router(actions.router, prefix="/api/v1")
    app.include_router(arbiter.router, prefix="/api/v1")
    app.include_router(monitors_routes.router, prefix="/api/v1")
    app.include_router(digest_routes.router, prefix="/api/v1")
    app.include_router(memory_routes.router, prefix="/api/v1")
    app.include_router(skills_optimization_routes.router, prefix="/api/v1")
    app.include_router(proactive_routes.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")
    app.include_router(mutations.router, prefix="/api/v1")
    app.include_router(job_truth.router, prefix="/api/v1")
    app.include_router(validation_harness.router, prefix="/api/v1")
    app.include_router(external_execution.router, prefix="/api/v1")
    app.include_router(telegram_soak.router, prefix="/api/v1")
    app.include_router(settings.router, prefix="/api/v1")
    app.include_router(runtime_config.router, prefix="/api/v1")
    app.include_router(model_selection.router, prefix="/api/v1")
    app.include_router(automation.router, prefix="/api/v1")
    app.include_router(connections.router, prefix="/api/v1")
    app.include_router(credentials.router, prefix="/api/v1")
    app.include_router(provider_topology.router, prefix="/api/v1")
    app.include_router(railway_discovery.router, prefix="/api/v1")
    app.include_router(railway_execution.router, prefix="/api/v1")
    app.include_router(catalog.router, prefix="/api/v1")
    app.include_router(telegram.router, prefix="/api/v1")
    app.include_router(slack.router, prefix="/api/v1")
    app.include_router(channels.router, prefix="/api/v1")
    app.include_router(autonomous_execution.router, prefix="/api/v1")
    app.include_router(browser.router, prefix="/api/v1")
    app.include_router(research.router, prefix="/api/v1")
    app.include_router(workspaces.router, prefix="/api/v1")
    app.include_router(deployment_targets.router, prefix="/api/v1")
    app.include_router(governance_diagnostics.router, prefix="/api/v1")
    app.include_router(workspace.router, prefix="/api/v1")
    app.include_router(agents.router, prefix="/api/v1")
    app.include_router(engineering.router, prefix="/api/v1")
    app.include_router(intelligence.router, prefix="/api/v1")
    app.include_router(cross_provider_correlation.router, prefix="/api/v1")
    app.include_router(mission_control.router, prefix="/api/v1")
    app.include_router(mission_control_live.router, prefix="/api/v1")
    app.include_router(reliability.router, prefix="/api/v1")
    app.include_router(operational_truth.router, prefix="/api/v1")
    app.include_router(enterprise.router, prefix="/api/v1")
    app.include_router(production.router, prefix="/api/v1")
    app.include_router(orgs.router, prefix="/api/v1")
    app.include_router(observability.router, prefix="/api/v1")
    app.include_router(plugins.router, prefix="/api/v1")
    app.include_router(human.router, prefix="/api/v1")
    app.include_router(presence.router, prefix="/api/v1")
    app.include_router(legacy.router, prefix="/api/v1")
    app.include_router(legacy.router, prefix="/api")


async def _deferred_startup(app: FastAPI) -> None:
    """Mount heavy routers and start background executors after /health is live."""
    global _deferred_bootstrap_complete
    settings = get_settings()
    _mount_deferred_routes(app)

    from aethos_core.execution_brain.agent_tool_executor import readonly_agent_tool_schemas

    canvas_flag = bool(getattr(settings, "canvas_surface_enabled", False))
    canvas_in_schema = any(
        str(t.get("name", "")) == "canvas_render" for t in readonly_agent_tool_schemas()
    )
    _log.info(
        "canvas_surface_enabled=%s canvas_render in agent schema=%s",
        canvas_flag,
        canvas_in_schema,
    )

    from aethos_core.connections.credential_hydration import hydrate_credentials_at_startup
    from aethos_core.runtime.browser_executor import browser_executor
    from aethos_core.runtime.browser_runtime_cleanup import browser_runtime_cleanup
    from aethos_core.runtime.job_executor import job_executor

    hydrate_credentials_at_startup(validate=True)
    job_executor.start()
    browser_executor.start()

    # Warm the Playwright launch probe once on the browser executor thread. The System
    # Health snapshot uses an import-only probe (cheap, no launch) and would otherwise
    # report "Execution ready: No / Launch probe: Failed" until the first real browser
    # op — even when Chromium is installed and launches fine. Warming records success so
    # the snapshot reflects true capability immediately. Best-effort; never blocks startup.
    try:
        from aethos_core.runtime.browser_diagnostics import (
            probe_playwright_on_browser_thread,
            record_browser_operation_success,
        )

        _warm = probe_playwright_on_browser_thread()
        if _warm.get("execution_ready"):
            record_browser_operation_success()
            _log.info("Browser runtime warm probe OK — Playwright execution ready.")
        else:
            _log.warning(
                "Browser runtime warm probe not ready: %s",
                _warm.get("user_message") or _warm.get("runtime_error_kind"),
            )
    except Exception as exc:  # noqa: BLE001 — diagnostics warm-up must never crash startup
        _log.warning("Browser runtime warm probe failed: %s", exc.__class__.__name__)

    from aethos_core.runtime.browser_profile_store import load_profiles_from_disk_at_startup

    load_profiles_from_disk_at_startup()
    browser_runtime_cleanup.start()
    from aethos_core.runtime.tunnel.tunnel_manager import bootstrap_tunnel_on_startup

    bootstrap_tunnel_on_startup()
    from aethos_core.runtime.schedulers.observation_scheduler import start_observation_scheduler

    start_observation_scheduler()
    from aethos_core.runtime.schedulers.automation_scheduler import start_automation_scheduler

    start_automation_scheduler()
    from aethos_core.runtime.resilience.schema_migrations import run_pending_migrations

    run_pending_migrations()
    from aethos_core.canvas.canvas_store import init_canvas_store_schema

    init_canvas_store_schema()
    from aethos_core.security.credential_vault import reload_credential_vault_from_disk

    reload_credential_vault_from_disk()
    from aethos_core.storage.hosted_store_guard import validate_hosted_shared_stores_at_startup

    validate_hosted_shared_stores_at_startup()
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts

    load_identity_contracts()
    from aethos_core.operational_skill_runtime import bootstrap_operational_runtime

    bootstrap_operational_runtime()
    from aethos_core.autonomous_execution.dispatcher_loop import start_autonomous_dispatcher_loop

    start_autonomous_dispatcher_loop()
    _deferred_bootstrap_complete = True
    _log.info("deferred API bootstrap complete")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from aethos_core.observability.telemetry import configure_telemetry
    from aethos_core.runtime.workspace_diagnostics import mark_api_started

    configure_telemetry()
    mark_api_started()

    bootstrap_task = asyncio.create_task(_deferred_startup(_app))
    yield

    if not bootstrap_task.done():
        bootstrap_task.cancel()
        try:
            await bootstrap_task
        except asyncio.CancelledError:
            pass

    if _deferred_bootstrap_complete:
        from aethos_core.autonomous_execution.dispatcher_loop import stop_autonomous_dispatcher_loop

        stop_autonomous_dispatcher_loop()
        from aethos_core.runtime.browser_session import browser_session_store
        from aethos_core.runtime.tunnel.tunnel_manager import shutdown_tunnel

        shutdown_tunnel()
        from aethos_core.runtime.schedulers.observation_scheduler import stop_observation_scheduler

        stop_observation_scheduler()
        from aethos_core.runtime.schedulers.automation_scheduler import stop_automation_scheduler

        stop_automation_scheduler()
        from aethos_core.runtime.browser_runtime_cleanup import browser_runtime_cleanup
        from aethos_core.runtime.browser_executor import browser_executor
        from aethos_core.runtime.job_executor import job_executor

        browser_runtime_cleanup.cleanup_all()
        browser_runtime_cleanup.stop()
        browser_executor.stop()
        browser_session_store.close_all()
        job_executor.stop()


app = FastAPI(title="AethOS", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-tenancy — bind the per-request tenant ContextVar from request.state.user.
# Registered first ⇒ innermost ⇒ runs *after* auth (user is set) and wraps the
# route handler. No-op (tenant = "default") unless MULTI_TENANT_ENABLED.
from aethos_core.tenancy.middleware import tenant_context_middleware  # noqa: E402

app.middleware("http")(tenant_context_middleware)

# §7 RBAC — least-privilege enforcement on mutating requests. Registered before
# the auth middleware so it runs *after* auth in the chain (request.state.user is
# set). No-op unless AUTH_ENABLED.
from aethos_core.security.rbac import rbac_middleware  # noqa: E402

app.middleware("http")(rbac_middleware)

# §2 Enterprise auth — enforce server-side sessions on protected routes when
# AUTH_ENABLED. No-op (pass-through) by default so existing deploys are unchanged.
from aethos_core.api.routes.aethos_identity import auth_session_middleware  # noqa: E402

app.middleware("http")(auth_session_middleware)

# §4 Rate limiting & abuse protection — registered after auth so it runs first
# (outermost), throttling abusive callers before any auth/work. Loopback exempt.
from aethos_core.api.rate_limit import rate_limit_middleware  # noqa: E402

app.middleware("http")(rate_limit_middleware)

# §5 Transport security headers — registered last so it is the outermost layer
# and stamps headers on every response (including 401/429 from inner layers).
from aethos_core.api.security_headers import security_headers_middleware  # noqa: E402

app.middleware("http")(security_headers_middleware)

_mount_core_routes(app)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "AethOS", "status": "ok", "docs": "/docs"}


@app.get("/version")
def root_version() -> dict[str, str]:
    from aethos_core.api.routes.health import get_app_version

    return get_app_version()


def _redirect_to_web_verify_email(request: Request, token: str = "") -> RedirectResponse:
    """When a verification link hits the API host, forward to the public web page."""
    from urllib.parse import urlparse

    from aethos_core.auth.email_verification import build_verification_url, public_app_url

    tok = (token or "").strip()
    url = build_verification_url(request, tok) if tok else public_app_url(request, "/verify-email")

    target = urlparse(url)
    req = urlparse(str(request.url))
    if target.netloc == req.netloc and target.path == req.path:
        from fastapi.responses import HTMLResponse

        return HTMLResponse(
            content=(
                "<html><body><p>Email verification</p>"
                f"<p><a href=\"{url}\">Open verification link</a></p></body></html>"
            ),
            status_code=200,
        )
    return RedirectResponse(url=url, status_code=302)


@app.get("/verify-email")
def verify_email_web_landing(request: Request, token: str = "") -> RedirectResponse:
    return _redirect_to_web_verify_email(request, token)


@app.get("/aethos/verify-email")
def verify_email_web_landing_prefixed(request: Request, token: str = "") -> RedirectResponse:
    return _redirect_to_web_verify_email(request, token)
