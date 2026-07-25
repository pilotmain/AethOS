# SPDX-License-Identifier: Apache-2.0
"""Single runtime authority — health, auth snapshot, chat readiness."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time


class TransportState(str, Enum):
    UNKNOWN = "unknown"
    REACHABLE = "reachable"
    UNREACHABLE = "unreachable"


class AuthState(str, Enum):
    UNKNOWN = "unknown"
    VALID = "valid"
    INVALID = "invalid"


class PanelState(str, Enum):
    """Observational only — must not gate chat."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    TIMEOUT = "timeout"


@dataclass
class RuntimeSnapshot:
    transport: TransportState = TransportState.UNKNOWN
    auth: AuthState = AuthState.UNKNOWN
    panel: PanelState = PanelState.HEALTHY
    provider_available: bool = False
    last_health_ok_at: float | None = None
    chat_ready: bool = False
    label: str = "Checking…"


class RuntimeAuthority:
    """One owner for runtime truth. Mission Control will subscribe later."""

    def __init__(self) -> None:
        self._snap = RuntimeSnapshot()
        self._browser_automation = False
        self._host_executor = False
        self._vercel_cli = False

    def configure_capabilities(
        self,
        *,
        browser_automation: bool,
        host_executor: bool,
        vercel_cli: bool,
        provider_available: bool,
    ) -> None:
        self._browser_automation = browser_automation
        self._host_executor = host_executor
        self._vercel_cli = vercel_cli
        self._snap.provider_available = provider_available
        self._recompute()

    def record_health_ok(self) -> None:
        self._snap.transport = TransportState.REACHABLE
        self._snap.last_health_ok_at = time()
        self._recompute()

    def record_health_fail(self) -> None:
        if self._snap.last_health_ok_at and time() - self._snap.last_health_ok_at < 300:
            return
        self._snap.transport = TransportState.UNREACHABLE
        self._recompute()

    def record_auth_valid(self) -> None:
        self._snap.auth = AuthState.VALID
        self._recompute()

    def record_auth_invalid(self) -> None:
        self._snap.auth = AuthState.INVALID
        self._recompute()

    def record_panel_state(self, state: PanelState) -> None:
        """Does not affect chat_ready."""
        self._snap.panel = state
        self._recompute()

    def snapshot(self) -> RuntimeSnapshot:
        return self._snap

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "browser_automation_enabled": self._browser_automation,
            "host_executor_enabled": self._host_executor,
            "vercel_cli_on_path": self._vercel_cli,
        }

    def _recompute(self) -> None:
        chat_ok = (
            self._snap.transport in (TransportState.REACHABLE, TransportState.UNKNOWN)
            and self._snap.auth != AuthState.INVALID
        )
        self._snap.chat_ready = chat_ok
        if self._snap.transport == TransportState.UNREACHABLE:
            self._snap.label = "API offline"
        elif self._snap.auth == AuthState.INVALID:
            self._snap.label = "Reconnect required"
        elif self._snap.panel != PanelState.HEALTHY:
            self._snap.label = "Connected · Some panels delayed"
        elif self._snap.transport == TransportState.REACHABLE:
            self._snap.label = "Connected"
        else:
            self._snap.label = "Checking…"


    def propose_action(
        self,
        action_type: str,
        params: dict | None = None,
        *,
        source: str = "chat",
        session_id: str = "default",
    ):
        from aethos_core.runtime.actions import action_store

        return action_store.propose(
            action_type, params, source=source, session_id=session_id
        )

    def list_action_events(
        self,
        *,
        action_ids: list[str] | None = None,
        session_id: str | None = None,
        since: float = 0.0,
    ) -> list[dict]:
        from aethos_core.runtime.actions import action_store

        return action_store.list_events(
            action_ids=action_ids, session_id=session_id, since=since
        )

    def approve_action(self, action_id: str):
        from aethos_core.runtime.actions import action_store

        return action_store.approve(
            action_id,
            host_executor_enabled=self._host_executor,
            vercel_cli_on_path=self._vercel_cli,
        )

    def deny_action(self, action_id: str):
        from aethos_core.runtime.actions import action_store

        return action_store.deny(action_id)

    def list_actions_grouped(self) -> dict:
        from aethos_core.runtime.actions import action_store

        return action_store.list_grouped()

    def create_job(
        self,
        *,
        title: str,
        job_type: str,
        params: dict | None = None,
        source: str = "chat",
        session_id: str = "default",
        auto_run: bool = True,
    ):
        from aethos_core.runtime.jobs import job_store

        return job_store.create(
            title=title,
            job_type=job_type,
            params=params,
            source=source,
            session_id=session_id,
            auto_run=auto_run,
        )

    def cancel_job(self, job_id: str):
        from aethos_core.runtime.jobs import job_store

        return job_store.cancel(job_id)

    def list_jobs_grouped(self) -> dict:
        from aethos_core.runtime.jobs import job_store

        return job_store.list_grouped()

    def list_job_events(
        self,
        *,
        job_ids: list[str] | None = None,
        session_id: str | None = None,
        since: float = 0.0,
    ) -> list[dict]:
        from aethos_core.runtime.jobs import job_store

        return job_store.list_events(job_ids=job_ids, session_id=session_id, since=since)

    def approve_preflight_readonly_execution(self, preflight_job_id: str):
        from aethos_core.operations.preflight_execution import approve_preflight_readonly_execution

        preflight, execution = approve_preflight_readonly_execution(preflight_job_id)
        return {"preflight_job": preflight.to_dict(), "execution_job": execution.to_dict()}

    def approve_mutation_execution(self, preflight_job_id: str):
        from aethos_core.operations.mutations.mutation_execution_flow import approve_mutation_execution

        preflight, execution = approve_mutation_execution(preflight_job_id)
        return {"preflight_job": preflight.to_dict(), "mutation_execution_job": execution.to_dict()}

    def approve_provider_e2e_orchestration(self, job_id: str):
        from aethos_core.provider_e2e_orchestration.approval_flow import approve_provider_e2e_orchestration

        job, meta = approve_provider_e2e_orchestration(job_id)
        return {"orchestration_job": job.to_dict(), **meta}

    def approve_railway_greenfield_preflight(
        self,
        job_id: str,
        *,
        session_id: str | None = None,
        remembered: dict | None = None,
    ):
        from aethos_core.providers.railway.greenfield_deployment.greenfield_approval_flow import (
            approve_railway_greenfield_preflight,
        )

        job, meta = approve_railway_greenfield_preflight(
            job_id,
            session_id=session_id,
            remembered=remembered,
        )
        return {"greenfield_preflight_job": job.to_dict(), **meta}

    def approve_vercel_greenfield_preflight(
        self,
        job_id: str,
        *,
        session_id: str | None = None,
        remembered: dict | None = None,
    ):
        from aethos_core.providers.vercel.greenfield_deployment.greenfield_preflight import (
            approve_vercel_greenfield_preflight,
        )

        job, meta = approve_vercel_greenfield_preflight(
            job_id,
            session_id=session_id,
            remembered=remembered,
        )
        return {"greenfield_preflight_job": job.to_dict(), **meta}

    def approve_supabase_env_completion(self, job_id: str):
        from aethos_core.provider_e2e_orchestration.env_completion.supabase_approval import (
            approve_supabase_env_completion,
        )

        job, meta = approve_supabase_env_completion(job_id)
        return {"supabase_env_completion_job": job.to_dict(), **meta}


# Process singleton
authority = RuntimeAuthority()
