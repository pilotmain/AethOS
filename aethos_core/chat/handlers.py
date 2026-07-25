# SPDX-License-Identifier: Apache-2.0
"""Deterministic reply handlers — no provider, no MC."""

from __future__ import annotations

import re

from aethos_core.identity.capability_language import (
    build_capability_overview,
    describe_browser_observation,
    describe_execution_runtime,
    describe_generative_intelligence,
    describe_vercel_cli,
    runtime_status_lines,
)
from aethos_core.identity.introduction_engine import greeting_reply as identity_greeting_reply
from aethos_core.identity.introduction_engine import is_returning_session, who_are_you_reply
from aethos_core.runtime.authority import authority


def _pack(reply: str, intent: str, meta: dict[str, str] | None = None) -> tuple[str, str, dict[str, str]]:
    return reply, intent, meta or {}


def greeting_reply(text: str, *, session_id: str = "default") -> str:
    from aethos_core.relational.conversational_memory import recent_context

    returning = is_returning_session(recent_context(session_id=session_id))
    return identity_greeting_reply(text=text, returning=returning)


def capability_matrix_reply(*, session_id: str = "default", text: str = "") -> str:
    from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_intent import (
        is_general_capability_question,
    )
    from aethos_core.identity.plain_capability_intro import (
        compose_plain_capability_overview_reply,
        compose_provider_connection_status_reply,
        is_provider_connection_question,
    )

    if is_provider_connection_question(text):
        return compose_provider_connection_status_reply(session_id=session_id)
    if is_general_capability_question(text):
        return compose_plain_capability_overview_reply(session_id=session_id)

    from aethos_core.provider.completion import provider_configured

    return build_capability_overview(authority.capabilities, generative_configured=provider_configured())


def identity_reply() -> str:
    return who_are_you_reply()


def vercel_login_health_reply() -> str:
    caps = authority.capabilities
    lines = [
        "**Vercel login / service health**",
        "",
    ]
    if not caps["browser_automation_enabled"]:
        lines.append(
            "I cannot log into your **private Vercel dashboard** unless governed browser observation is "
            "enabled and you approve using an authenticated session."
        )
    else:
        lines.append(
            "Governed browser observation is **available** — I can open the Vercel dashboard after your **approval**."
        )
    lines.extend(
        [
            "",
            "I can help in three ways:",
            "1. Check **public Vercel platform status** (no login): https://www.vercel-status.com/",
        ]
    )
    if caps["host_executor_enabled"] and caps["vercel_cli_on_path"]:
        lines.append(
            "2. Run **read-only CLI checks** with approval: `vercel whoami`, `vercel project ls`."
        )
    elif caps["host_executor_enabled"]:
        lines.append("2. Install/authenticate the **Vercel CLI** (`vercel login`) for terminal checks.")
    else:
        lines.append("2. Enable **governed execution runtime** and install the Vercel CLI for terminal checks.")
    if not caps["browser_automation_enabled"]:
        lines.append("3. Enable **governed browser observation** in `.env`, then restart the API.")
    else:
        lines.append("3. Use **governed browser observation** after approval for dashboard health.")
    lines.extend(
        [
            "",
            "**Current operational pathways**",
            f"- {describe_browser_observation(enabled=caps['browser_automation_enabled'])}",
            f"- {describe_execution_runtime(enabled=caps['host_executor_enabled'])}",
            f"- {describe_vercel_cli(available=caps['vercel_cli_on_path'])}",
        ]
    )
    return "\n".join(lines)


def public_vercel_status_reply() -> str:
    return (
        "**Public Vercel status** (no login)\n\n"
        "Official status page: https://www.vercel-status.com/\n\n"
        "For project-specific health, use the Vercel CLI or dashboard after approval."
    )


def terminal_access_reply() -> str:
    caps = authority.capabilities
    return describe_execution_runtime(enabled=caps["host_executor_enabled"])


def model_config_reply() -> str:
    from aethos_core.config import get_settings
    from aethos_core.provider.completion import provider_configured

    s = get_settings()
    prov = "available" if provider_configured() else "not available"
    return (
        "**Operational intelligence configuration**\n\n"
        f"- Generative intelligence enabled: **`{s.use_real_llm}`**\n"
        f"- Active provider: **`{s.active_provider}`**\n"
        f"- Provider ready: **`{prov}`**\n"
        f"- Model: **`{s.anthropic_model}`**\n\n"
        "Capability questions use governed operational responses. "
        "Open-ended reasoning uses generative intelligence when available."
    )


def runtime_status_reply() -> str:
    snap = authority.snapshot()
    caps = authority.capabilities
    lines = ["**Operational runtime status**", ""] + runtime_status_lines(
        caps,
        connection=snap.label,
        chat_ready=snap.chat_ready,
        provider_available=snap.provider_available,
    )
    return "\n".join(lines)


def setup_reply() -> str:
    return (
        "**Setup (local MVP)**\n\n"
        "1. `python3 -m venv .venv && source .venv/bin/activate`\n"
        "2. `pip install -e \".[dev]\"`\n"
        "3. Copy `.env.example` → `.env` (optional: `USE_REAL_LLM`, `ANTHROPIC_API_KEY`)\n"
        "4. `uvicorn aethos_core.api.main:app --reload --port 8010`\n"
        "5. `cd web && npm install && npm run dev`\n\n"
        "See `docs/SETUP.md` for details."
    )


def need_from_me_reply(text: str) -> str:
    lower = (text or "").lower()
    if "vercel" in lower:
        lines = [
            "**What I need from you (Vercel checks)**",
            "",
            "Pick one path:",
            "1. **Public status only** — no credentials needed.",
            "2. **CLI checks** — Vercel CLI installed and authenticated (`vercel login`).",
            "3. **Dashboard review** — browser automation enabled + your approval.",
        ]
        caps = authority.capabilities
        if not caps["vercel_cli_on_path"]:
            lines.append("\nInstall CLI: `npm i -g vercel` then `vercel login`.")
        if not caps["browser_automation_enabled"]:
            lines.append("Enable browser automation in `.env` for dashboard access.")
        return "\n".join(lines)
    return (
        "**What I need from you**\n\n"
        "Tell me the outcome you want (check status, deploy, configure runtime, or plan work). "
        "For actions that touch your machine or accounts, I will ask for explicit approval."
    )


def website_login_reply() -> str:
    caps = authority.capabilities
    if caps["browser_automation_enabled"]:
        return (
            "Yes — with **governed browser observation** enabled I can open allowed websites after your approval. "
            "I will not use stored credentials without explicit consent per task."
        )
    return (
        "Not yet — **governed browser observation is restricted**. Enable it in `.env`, restart the API, "
        "then ask again. Public status pages work without login."
    )


def job_status_reply(text: str) -> str:
    import re

    from aethos_core.runtime.jobs import job_store

    m = re.search(r"\b(job-[a-f0-9]+)\b", text, re.I)
    if not m:
        return "Provide a job id, e.g. `status of job-...`"
    jid = m.group(1)
    job = job_store.get(jid)
    if not job:
        return f"No job found for `{jid}`."
    lines = [
        f"**Job `{jid}`**",
        f"- Status: **{job.status.value}**",
        f"- Type: **{job.job_type}**",
        f"- Title: {job.title}",
    ]
    if job.result:
        lines.append(f"- Result: {job.result.splitlines()[0]}")
    if job.failure_reason:
        lines.append(f"- Failure: {job.failure_reason}")
    return "\n".join(lines)


def action_status_reply(text: str) -> str:
    import re

    from aethos_core.runtime.actions import action_store

    m = re.search(r"\b(act-[a-f0-9]+)\b", text, re.I)
    if not m:
        return "Provide an action id, e.g. `what happened to act-...`"
    aid = m.group(1)
    action = action_store.get(aid)
    if not action:
        return f"No action found for `{aid}`."
    lines = [
        f"**Action `{aid}`**",
        f"- Status: **{action.status.value}**",
        f"- Type: **{action.action_type}**",
        f"- Summary: {action.summary}",
    ]
    if action.result:
        lines.append(f"- Result: {action.result.splitlines()[0]}")
    if action.error:
        lines.append(f"- Error: {action.error}")
    if action.status.value == "pending":
        lines.append("\nApprove or deny in **Mission Control → Jobs**.")
    if action.status.value == "denied":
        lines.append("\nThis action was denied by the operator.")
    return "\n".join(lines)


def deploy_railway_reply() -> str:
    """Railway deploy+env truth — PROVIDER_DEPLOY_CHAT_TRUTH_ALIGNMENT_FIX."""
    return "\n".join(
        [
            "**Railway capability — honest answer**",
            "",
            "No full one-shot deploy + generic env var configuration + final report from natural language today.",
            "",
            "**Supported today (with governance where noted):**",
            "- Restart or **redeploy an existing Railway service** — after Mission Control preflight and your approval",
            "- Discovery — projects, services, environments, deployments",
            "- Logs and deployment status — readonly inspection",
            "- Verification evidence — under governed restart/redeploy flows",
            "",
            "**Not supported from this request:**",
            "- Generic env var writes (`set_env_var` disabled platform-wide)",
            "- Production env var mutation from chat",
            "- Combined deploy + env + report as one unstructured NL flow",
            "",
            "**Available on a separate governed path:** FIX 112 staging env configure (secure store + execution contract only).",
            "",
            "**Valid next steps:**",
            "- `run railway deployment readiness checks`",
            "- `check railway env value readiness`",
            "- `redeploy the Railway <service> service`",
            "- Ask for a missing-configuration report if your Railway token or target service is not set up",
        ]
    )


def deploy_vercel_reply() -> str:
    """Level 2 Vercel deploy truth — PROVIDER_DEPLOY_CHAT_TRUTH_ALIGNMENT_FIX."""
    return "\n".join(
        [
            "**Vercel capability — honest answer**",
            "",
            "No full E2E Vercel env + deploy + verify flow today.",
            "",
            "**Supported today:**",
            "- Connect and validate a Vercel API token (Mission Control → Advanced settings → Credentials)",
            "- Inspect projects, deployments, domains, and deployment status",
            "- Read environment variable **keys and targets** — never secret values",
            "- **Redeploy an existing production-linked Vercel project** — after Mission Control preflight, "
            "your approval, and production mutation gates",
            "",
            "**Not supported today:**",
            "- Add, update, or remove Vercel environment variables (writes disabled platform-wide)",
            "- Deploy from an arbitrary Git branch (`deploy_from_git` disabled)",
            "- Create/link projects or greenfield deploy-from-scratch in one step",
            "",
            "**Valid next steps:**",
            "- Inspect your Vercel project and latest deployment status",
            "- Say redeploy with a specific existing project name to start governed preflight",
            "- Configure env vars manually in the Vercel dashboard until env write support ships",
            "- Ask what capability is missing if Connections shows no validated token",
        ]
    )


def resolve_handler(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    """Return (reply, intent, meta) or None if Lane B required."""
    from aethos_core.chat import lanes as lane_mod
    from aethos_core.chat.action_prompts import (
        propose_browser_automation_enable,
        propose_host_executor_enable,
        propose_terminal_probe_reply,
        propose_vercel_cli_probe_reply,
    )
    from aethos_core.chat.deterministic import match_project_template
    from aethos_core.chat.lanes import is_ultra_fast_prompt, should_bypass_provider_stream

    raw = (text or "").strip()
    if not raw:
        return None

    # §5 — an explicit "render … on the canvas" prompt is an agent-tool intent
    # (canvas_render lives in the agent runtime). Decline here so it is not claimed
    # by the ultra-fast / capability responder and reaches Step 3 to actually draw.
    from aethos_core.chat.front_door_intent import is_canvas_render_request

    if is_canvas_render_request(raw):
        return None

    from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn

    kernel = route_operational_conversation_kernel_turn(raw, session_id=session_id)
    if kernel is not None:
        meta = {k: str(v) for k, v in (kernel.meta or {}).items()}
        return _pack(kernel.reply, kernel.intent, meta)

    from aethos_core.runtime.runtime_config_intent import is_runtime_provider_config_question

    if is_runtime_provider_config_question(raw):
        from aethos_core.runtime_truth_alignment.runtime_truth_alignment_router import (
            route_runtime_truth_alignment,
        )

        truth = route_runtime_truth_alignment(raw, session_id=session_id)
        if truth is not None:
            reply, intent, meta = truth
            return _pack(reply, intent, {k: str(v) for k, v in meta.items()})
        return _pack(model_config_reply(), "runtime_config_query")

    from aethos_core.post_mutation_verification.global_verification_preemption import (
        route_global_verification_query,
    )

    verification = route_global_verification_query(raw, session_id=session_id)
    if verification is not None:
        meta = {k: str(v) for k, v in (verification.meta or {}).items()}
        return _pack(verification.reply, verification.intent, meta)

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_hard_preemption,
        route_workflow_discovery_followup,
    )

    hard_workflow = route_workflow_discovery_hard_preemption(raw, session_id=session_id)
    if hard_workflow is not None:
        reply, intent, meta = hard_workflow
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.repair_memory.repair_outcome_router import route_repair_outcome_question

    repair_outcome = route_repair_outcome_question(raw, session_id=session_id)
    if repair_outcome is not None:
        meta = {k: str(v) for k, v in (repair_outcome.meta or {}).items()}
        return _pack(repair_outcome.reply, repair_outcome.intent, meta)

    from aethos_core.browser_observation.browser_observation_router import (
        is_browser_observation_lane_intent,
        route_browser_observation_lane,
    )

    if is_browser_observation_lane_intent(raw):
        observation = route_browser_observation_lane(raw, session_id=session_id)
        if observation is not None:
            reply, intent, meta = observation
            return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.chat.operational_master_router import resolve_operational_master_route

    master = resolve_operational_master_route(raw, session_id=session_id)
    if master is not None:
        return _pack(master.reply, master.intent, master.meta)

    from aethos_core.runtime.operational_memory import operational_memory

    correction_reply, applied = operational_memory.apply_user_correction(raw)
    if applied:
        return _pack(correction_reply, "vercel_memory_correction", {})

    from aethos_core.continuity_intelligence.conversational_identity_runtime import compose_conversational_identity_reply

    identity_reply = compose_conversational_identity_reply(raw, session_id=session_id)
    if identity_reply is not None:
        reply, intent, meta = identity_reply
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.providers.github.mutations.rerun_intent_continuation import compose_github_workflow_rerun_route_reply

    github_rerun = compose_github_workflow_rerun_route_reply(raw, session_id=session_id)
    if github_rerun is not None:
        reply, intent, meta = github_rerun
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.provider_readonly_intent.readonly_provider_router import compose_readonly_provider_route_reply

    readonly_provider = compose_readonly_provider_route_reply(raw, session_id=session_id)
    if readonly_provider is not None:
        reply, intent, meta = readonly_provider
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.providers.github.workflow_discovery.workflow_creation_plan import (
        route_workflow_creation_from_context,
    )

    creation_ctx = route_workflow_creation_from_context(raw, session_id=session_id)
    if creation_ctx is not None:
        reply, intent, meta = creation_ctx
        from aethos_core.chat.route_trace import save_last_route_trace as _save_ctx_trace

        _save_ctx_trace(session_id=session_id, meta=meta, intent=intent)
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.providers.github.mutations.rerun_no_execution_followup import (
        compose_rerun_no_execution_followup,
    )

    no_exec = compose_rerun_no_execution_followup(raw, session_id=session_id)
    if no_exec is not None:
        reply, intent, meta = no_exec
        from aethos_core.chat.route_trace import save_last_route_trace

        save_last_route_trace(session_id=session_id, meta=meta, intent=intent)
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        route_workflow_discovery_followup,
    )

    workflow_discovery = route_workflow_discovery_followup(raw, session_id=session_id)
    if workflow_discovery is not None:
        reply, intent, meta = workflow_discovery
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.provider_topology.followup_lock import compose_thread_continuation_reply

    thread_lock = compose_thread_continuation_reply(raw, session_id=session_id)
    if thread_lock is not None:
        reply, intent, meta = thread_lock
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.approval.session_scopes import compose_session_scope_reply

    scope_reply = compose_session_scope_reply(raw, session_id=session_id)
    if scope_reply is not None:
        reply, intent, meta = scope_reply
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.chat.agent_intelligence import multi_agent_reply

    multi_agent = multi_agent_reply(raw, session_id=session_id)
    if multi_agent is not None:
        reply, intent, meta = multi_agent
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.chat.local_workspace_prompts import local_workspace_reply

    workspace = local_workspace_reply(raw, session_id=session_id)
    if workspace is not None:
        reply, intent, meta = workspace
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.jobs.pending_job_approval_resolution import route_short_approval_turn

    short_approval = route_short_approval_turn(raw, session_id=session_id)
    if short_approval is not None:
        reply, intent, meta = short_approval
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.jobs.job_approval_guidance import compose_job_approval_guidance_reply, is_job_approval_intent

    if is_job_approval_intent(text) and not re.search(
        r"\bwhy\s+(?:can'?t|cannot)\s+i\s+approve\b|\bwhy\s+is\s+(?:it|this)\s+not\s+approvable\b",
        text,
        re.I,
    ):
        approval_reply = compose_job_approval_guidance_reply(raw, session_id=session_id)
        if approval_reply:
            return _pack(approval_reply, "job_approval_guidance")

    from aethos_core.operation_lifecycle.lifecycle_followup_router import compose_lifecycle_followup_reply

    lifecycle_reply = compose_lifecycle_followup_reply(raw, session_id=session_id)
    if lifecycle_reply is not None:
        reply, intent, meta = lifecycle_reply
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.chat.mutation_target_chat import compose_target_update_reply, compose_why_not_approvable_reply

    why_blocked = compose_why_not_approvable_reply(raw, session_id=session_id)
    if why_blocked is not None:
        reply, intent, meta = why_blocked
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    target_update = compose_target_update_reply(raw, session_id=session_id)
    if target_update is not None:
        reply, intent, meta = target_update
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.chat.mutation_execution_chat import compose_mutation_execution_truth_reply

    exec_truth = compose_mutation_execution_truth_reply(raw, session_id=session_id)
    if exec_truth is not None:
        reply, intent, meta = exec_truth
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.devops_intent_planner.devops_capability_router import compose_devops_capability_route_reply

    devops_capability = compose_devops_capability_route_reply(raw, session_id=session_id)
    if devops_capability is not None:
        reply, intent, meta = devops_capability
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

    mutation_preflight = create_mutation_preflight_job_reply(raw, session_id=session_id)
    if mutation_preflight is not None:
        from aethos_core.operational_cognition.cognition_authority import cognition_authority_blocks_legacy_job

        if not cognition_authority_blocks_legacy_job(
            attempted_route="mutation_preflight",
            text=raw,
            session_id=session_id,
        ):
            return mutation_preflight

    from aethos_core.chat.capability_foundation_prompts import capability_foundation_reply

    foundation = capability_foundation_reply(raw)
    if foundation is not None:
        reply, intent, meta = foundation
        return _pack(reply, intent, {k: str(v) for k, v in meta.items()})

    from aethos_core.runtime.external_jobs import infer_external_health_from_text

    if infer_external_health_from_text(raw):
        from aethos_core.chat.job_prompts import create_external_health_job_reply
        from aethos_core.operational_cognition.cognition_authority import cognition_authority_blocks_legacy_job

        if not cognition_authority_blocks_legacy_job(
            attempted_route="external_health_job",
            text=raw,
            session_id=session_id,
        ):
            return create_external_health_job_reply(raw, session_id=session_id)

    from aethos_core.runtime.browser_intents import is_vercel_ambiguous_request
    from aethos_core.runtime.browser_intents import vercel_ambiguous_clarification_reply

    from aethos_core.chat.browser_prompts import create_browser_intent_reply
    from aethos_core.runtime.browser_jobs import infer_browser_intent_from_text

    if infer_browser_intent_from_text(raw):
        from aethos_core.operational_cognition.cognition_authority import cognition_authority_blocks_legacy_job

        if not cognition_authority_blocks_legacy_job(
            attempted_route="browser_intent_job",
            text=raw,
            session_id=session_id,
        ):
            browser_reply = create_browser_intent_reply(raw, session_id=session_id)
            if browser_reply is not None:
                return browser_reply

    if is_vercel_ambiguous_request(raw):
        return _pack(vercel_ambiguous_clarification_reply(), "vercel_ambiguous")

    if lane_mod._PROVIDER_JOB_RX.search(raw):
        from aethos_core.chat.job_prompts import create_provider_job_reply
        from aethos_core.operational_cognition.cognition_authority import cognition_authority_blocks_legacy_job

        if not cognition_authority_blocks_legacy_job(
            attempted_route="provider_job",
            text=raw,
            session_id=session_id,
        ):
            return create_provider_job_reply(raw, session_id=session_id)

    project = match_project_template(raw, session_id=session_id)
    if project is not None:
        return project

    if is_ultra_fast_prompt(raw):
        if raw.lower() in {"hi", "hello", "hey", "yo", "sup", "hola", "howdy"}:
            return _pack(greeting_reply(raw, session_id=session_id), "greeting")
        if re.search(r"\bwho are you\b", raw, re.I):
            return _pack(identity_reply(), "identity_intro")
        return _pack(capability_matrix_reply(session_id=session_id, text=raw), "capability_question")

    lower = raw.lower()
    if lane_mod._ACTION_STATUS_RX.search(raw):
        return _pack(action_status_reply(raw), "action_status")
    if re.search(r"\b(job-[a-f0-9]+)\b", raw, re.I) and re.search(
        r"\b(status|what happened|result)\b", raw, re.I
    ):
        return _pack(job_status_reply(raw), "job_status")
    if lane_mod._QUEUED_TRACKED_JOB_RX.search(raw):
        from aethos_core.chat.job_prompts import create_queued_tracked_job_reply

        return create_queued_tracked_job_reply(raw, session_id=session_id)
    if lane_mod._TRACKED_JOB_RX.search(raw):
        from aethos_core.chat.job_prompts import create_tracked_job_reply

        return create_tracked_job_reply(raw, session_id=session_id)
    if lane_mod._VERCEL_CLI_PROBE_RX.search(raw):
        return propose_vercel_cli_probe_reply(session_id)
    if lane_mod._TERMINAL_PROBE_RX.search(raw):
        return propose_terminal_probe_reply(session_id)
    if lane_mod._ENABLE_BROWSER_RX.search(raw):
        return propose_browser_automation_enable(session_id)
    if lane_mod._ENABLE_HOST_RX.search(raw):
        return propose_host_executor_enable(session_id)
    if lane_mod._RUNTIME_STATUS_RX.search(raw):
        from aethos_core.post_mutation_verification.global_verification_preemption import (
            verification_preemption_blocks_route,
        )

        if not verification_preemption_blocks_route(raw, session_id=session_id):
            return _pack(runtime_status_reply(), "runtime_status")
    if lane_mod._NEED_FROM_ME_RX.search(raw):
        return _pack(need_from_me_reply(raw), "clarification")
    if lane_mod._SETUP_RX.search(raw) and len(raw) < 220:
        return _pack(setup_reply(), "setup")
    if lane_mod._WEBSITE_LOGIN_RX.search(raw):
        return _pack(website_login_reply(), "capability_question")
    if lane_mod._DEPLOY_VERCEL_RX.search(raw):
        return _pack(deploy_vercel_reply(), "external_site_task")
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import classify_vercel_readonly_intent

    vercel_readonly = classify_vercel_readonly_intent(raw)
    if vercel_readonly is None and "vercel" in lower and (
        "login" in lower or "health" in lower or "service" in lower
    ):
        return _pack(vercel_login_health_reply(), "external_site_task")
    if "public" in lower and "vercel" in lower and "status" in lower:
        return _pack(public_vercel_status_reply(), "external_site_task")
    if should_bypass_provider_stream(raw):
        if is_runtime_provider_config_question(raw) or "model" in lower:
            return _pack(model_config_reply(), "runtime_config_query")
        if "terminal" in lower or "access" in lower:
            return _pack(terminal_access_reply(), "capability_question")
        if "vercel" in lower:
            return _pack(vercel_login_health_reply(), "external_site_task")
        return _pack(capability_matrix_reply(session_id=session_id, text=raw), "capability_question")

    return None
