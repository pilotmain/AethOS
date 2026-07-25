# SPDX-License-Identifier: Apache-2.0
"""Minimal settings — one config authority."""

from __future__ import annotations

from functools import lru_cache
import shutil
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Safe BYOK capabilities turned on when AETHOS_BATTERIES_INCLUDED=true (default).
_BATTERIES_INCLUDED_FLAGS: tuple[str, ...] = (
    "chat_streaming_enabled",
    "agent_runtime_enabled",
    "workspace_suite_enabled",
    "canvas_surface_enabled",
    "vector_memory_enabled",
    "model_foundry_enabled",
    "arbiter_enabled",
    "model_failover_enabled",
    "orchestration_board_delegate_enabled",
    "mcp_bridge_enabled",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AethOS"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8010

    # Batteries-included profile — safe, user-funded (BYOK) capabilities default ON.
    # Set false for a minimal operator deployment (channels, mutations, browser stay opt-in).
    aethos_batteries_included: bool = True

    use_real_llm: bool = False
    active_provider: str = "none"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    next_public_supabase_url: str = ""
    next_public_supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    # Account-level Supabase Management API Personal Access Token. ONE token works
    # across ALL the operator's projects (list/keys/provision). Prefer the vault
    # (provider "supabase") over this env field. The per-project fields above stay
    # supported for direct single-project DB wiring.
    supabase_access_token: str = ""

    # Canonical env: BROWSER_AUTOMATION_ENABLED
    browser_automation_enabled: bool = False
    browser_provider: str = "playwright"
    # Headless by default — hosted containers have no X server, so a headed launch fails with
    # "Missing X server or $DISPLAY". Local dev can set BROWSER_HEADLESS=false to watch it.
    browser_headless: bool = True
    # Settle delay (ms) after navigation before capturing — lets JS-rendered / lazy content
    # finish painting (SPAs render after DOMContentLoaded), so screenshots aren't blank.
    browser_capture_settle_ms: int = 2500
    browser_heartbeat_interval_sec: float = 5.0
    browser_heartbeat_stale_sec: float = 20.0
    browser_profiles_dir: str = "data/browser_profiles"
    browser_artifacts_dir: str = "data/browser_artifacts"
    browser_capture_approval_required: bool = False
    credential_live_validation_enabled: bool = True
    presentation_bypass_chat_enabled: bool = False
    presentation_bypass_mc_enabled: bool = True
    credentials_dir: str = "data/credentials"
    local_workspace_registry_dir: str = "data/local_workspace"
    local_workspace_artifacts_dir: str = "data/local_workspace_artifacts"
    deployment_targets_registry_dir: str = "data/deployment_targets"
    agent_artifacts_dir: str = "data/agent_artifacts"
    aethos_workspace_root: str = ""
    aethos_portfolio_root: str = ""
    host_executor_enabled: bool = False

    web_api_token: str = ""
    web_user_id: str = "web_local"

    job_max_runtime_sec: float = 300.0
    job_provider_timeout_sec: float = 90.0
    readonly_execution_timeout_sec: float = 120.0
    vercel_api_step_timeout_sec: float = 45.0
    url_reachability_timeout_sec: float = 12.0
    browser_fallback_step_timeout_sec: float = 20.0

    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_tunnel_enabled: bool = False
    tunnel_provider: str = "ngrok"
    ngrok_authtoken: str = ""
    ngrok_region: str = "us"
    ngrok_target_port: int = 8010
    ngrok_domain: str = ""

    # AGENTIC_EXECUTION_BRAIN_001 — governed reasoning layer (Railway pilot first)
    execution_brain_enabled: bool = True
    execution_brain_use_llm: bool = False
    execution_brain_railway_pilot_enabled: bool = True
    execution_brain_vercel_enabled: bool = False

    # Agent runtime — AethOS agent LLM tool loop for step-3 chat (BYOK; on with batteries included)
    agent_runtime_enabled: bool = True
    agent_context_compaction_enabled: bool = True
    agent_tool_loop_detection_enabled: bool = True

    # §1 Conversational continuation TTL — a pending task-frame continuation
    # (redeploy intent, pending action, …) may only answer a follow-up while it is
    # genuinely recent. After this many minutes it is treated as stale and yields
    # to the fresh turn, so an abandoned redeploy can never hijack a later request.
    continuation_ttl_minutes: int = 30

    # Durable agent jobs — run multi-agent coordination as a server-side durable
    # job (via runtime/job_executor) instead of synchronously inside the chat
    # request. The run then survives navigation / tab close; the UI subscribes to
    # the job's lifecycle and reattaches by job_id. On by default. When off,
    # multi-agent turns fall back to the legacy in-request execution.
    durable_agent_jobs_enabled: bool = True

    # §1 Prompt caching (Anthropic ephemeral cache_control) — cost + latency win.
    # On by default: caches the stable prefix (system prompt + tool catalog) so
    # repeat turns re-read it instead of re-billing it. retention "long" requests
    # the extended (1h) TTL via the Anthropic beta header; "short" is the 5m TTL.
    prompt_cache_enabled: bool = True
    prompt_cache_retention: str = "short"  # short | long

    # §2 Chat streaming — deliver the governed reply incrementally over SSE so
    # text renders token-by-token and is abortable mid-stream. Off by default;
    # the full governed pipeline (safety/grounding/footer/polish) runs unchanged
    # before streaming, so governance and tool-step rendering are preserved.
    chat_streaming_enabled: bool = True

    # §1 Live progress narration — emit human-readable step events from the agent
    # tool loop ("Listing your Railway projects… ✓ Found pilotos → aethos-api")
    # so the operator sees what AethOS is doing as it happens. Read-only
    # visibility only: it never executes anything and never bypasses approval.
    # Default on; when off, behavior is exactly today's (no events emitted).
    live_progress_enabled: bool = True

    # §C5 Per-turn latency telemetry. When on, the turn's time breakdown
    # (routing / model / tools / total) is stamped into the chat reply meta so the
    # UI can show "this turn took N ms" in verbose/trace mode. Phase timings are
    # always fed to observability/OTEL regardless of this flag (it only controls
    # whether the breakdown is surfaced in the reply meta).
    chat_verbose_timing_enabled: bool = False

    # §2 One model-driven chat loop — thin mutation gate + agent tool loop for all
    # other turns. Bypasses the legacy router scramble; output delivered as-is.
    chat_single_loop_enabled: bool = True

    # §B1 Governed multi-step deep research (planner → gather → synthesize → artifact).
    deep_research_enabled: bool = False

    # §9 Model failover — on rate-limit (429) / 5xx / timeout, retry the next
    # model in an ordered chain. Tokens still come from the user's vault keys (BYOK).
    model_failover_enabled: bool = True
    model_failover_chain: str = ""  # comma-separated model ids, highest priority first

    # §7 Orchestration board "delegate task" — spawn an on-demand agent from
    # Mission Control. Network-facing (runs read-only coordination).
    # The board's live visualization works regardless; only delegation needs this.
    orchestration_board_delegate_enabled: bool = True

    # OPERATIONAL_CONVERSATION_KERNEL_001 — session subject + readonly tool loop
    operational_conversation_kernel_enabled: bool = True
    kernel_router_retirement_enabled: bool = True
    vercel_reference_lane_enabled: bool = True
    kernel_reality_capture_enabled: bool = True
    # Staging-only: allow synthetic daily snapshot dates for accelerated soak (never enable in production)
    kernel_soak_dev_accelerate: bool = False

    # Phase 9.6/9.7 — governed mutation execution (off by default)
    mutation_execution_enabled: bool = False
    mutation_t3_production_enabled: bool = False

    # FUNCTIONALITY_REALITY_SPRINT_001 — provider E2E orchestration + env mutations
    provider_e2e_orchestration_enabled: bool = True
    provider_env_var_mutations_enabled: bool = True
    provider_e2e_poll_interval_sec: float = 0.5
    provider_e2e_poll_max_attempts: int = 20

    # AETHOS_SOLO_PRODUCTION_EXECUTION_MODE — local trusted developer fast path (off by default)
    aethos_solo_execution_mode: bool = False
    aethos_solo_execution_provider: str = ""
    aethos_solo_allowed_repos: str = "pilotmain/AethOS"
    aethos_solo_allowed_providers: str = "railway"
    aethos_solo_allowed_environments: str = "staging"
    aethos_solo_allow_production: bool = False
    aethos_solo_require_final_confirmation: bool = True
    aethos_solo_auto_approve: bool = False
    aethos_solo_auto_approve_phases: bool = False
    aethos_local_env_trusted: bool = False
    autonomous_execution_enabled: bool = False

    # Railway governed mutation credentials (optional env override)
    railway_api_token: str = ""
    railway_project_id: str = ""
    railway_environment_id: str = ""
    railway_service_id_api: str = ""
    # Provider mutation for governed restart: service_instance_redeploy (default) or deployment_restart
    railway_restart_provider_operation: str = "service_instance_redeploy"
    # Railway execution mode: api (GraphQL) or cli (railway CLI) — never silently switch
    railway_execution_mode: str = "api"
    railway_cli_path: str = "railway"

    # Railway greenfield service creation execution enablement (FIX 102)
    railway_greenfield_execution_enabled: bool = False
    railway_greenfield_execution_mode: str = "disabled"
    railway_greenfield_allowed_projects: str = "pilotos"
    railway_greenfield_allowed_environments: str = "staging,development"
    railway_greenfield_allow_production: bool = False
    railway_greenfield_allowed_services: str = ""
    railway_greenfield_require_final_phrase: bool = True
    # FIX 108B — emergency stop for all live greenfield mutations (default off)
    railway_greenfield_mutation_kill_switch: bool = False
    # FIX 109 — staging-only GitHub source binding (connect_source phase, default off)
    railway_greenfield_connect_source_enabled: bool = False
    # FIX 111 — live disconnect_repo_source rollback (default off; FIX 110 is dry-run only)
    railway_greenfield_disconnect_source_enabled: bool = False
    # FIX 115 — live revert_env_writes rollback (default off)
    railway_greenfield_revert_env_enabled: bool = False
    # FIX 112 — staging-only secure-store env writes (default off)
    railway_greenfield_configure_env_enabled: bool = False
    # FIX 113 — governed deploy trigger after env verification (default off)
    railway_greenfield_trigger_deploy_enabled: bool = False
    # FIX 114 — readonly runtime verification after deploy (default off)
    railway_greenfield_verify_runtime_enabled: bool = False

    # FIX 117 — production policy hardening (policy layer; live prod forward locked by default)
    railway_production_incident_mode: bool = False
    railway_production_deployment_freeze: bool = False
    railway_production_freeze_start_utc: str = ""
    railway_production_freeze_end_utc: str = ""
    railway_production_shadow_mode_required: bool = True
    railway_production_forward_live_unlocked: bool = False
    railway_production_operator_quorum: int = 2
    railway_production_require_second_confirmation: bool = True
    railway_production_audit_retention_days: int = 90
    railway_production_slo_verification_required: bool = True
    # FIX 118 — production shadow rehearsal (policy-complete, no live mutations)
    railway_production_shadow_execution: bool = False
    # FIX 119 — production verification hardening (multi-signal, no live prod mutation)
    railway_production_verification_min_strong_signals: int = 2
    railway_production_verification_min_signal_families: int = 3
    railway_production_verification_reject_weak_only: bool = True
    railway_production_verification_require_log_evidence: bool = True
    # FIX 120 — production rollback escalation (manual only, no autonomous rollback)
    railway_production_rollback_escalation_enabled: bool = True
    railway_production_rollback_rehearsal_quorum: int = 2
    railway_production_rollback_require_incident_commander_ack: bool = True
    # FIX 121 — multi-stage rollout orchestration (governed sequencing, no autonomous promotion)
    railway_production_rollout_orchestration_enabled: bool = True
    railway_production_rollout_require_verification: bool = True
    railway_production_rollout_require_escalation_clear: bool = True
    # FIX 122 — canary + shadow deployment policy (governed strategy, no traffic mutation)
    railway_production_canary_shadow_policy_enabled: bool = True
    railway_production_max_canary_percent: int = 5
    railway_production_canary_promotion_pause_error_rate: float = 0.05
    railway_production_require_synthetic_verification_traffic: bool = True
    railway_production_shadow_traffic_mirror_simulation: bool = True
    # FIX 123 — production incident command (human escalation, no autonomous mutation)
    railway_production_incident_command_enabled: bool = True
    railway_production_incident_default_severity: str = "sev2"
    # FIX 125A — software delivery issue → plan lane (planning only; isolated from infra)
    software_delivery_issue_plan_enabled: bool = True
    software_delivery_require_planning_approval: bool = True
    # FIX 125B — governed branch orchestration (workspace layer; no code/PR/merge)
    software_delivery_branch_orchestration_enabled: bool = True
    software_delivery_branch_require_planning_approved: bool = True
    # FIX 125C — patch proposal + diff preview (no file writes / commit / PR / deploy)
    software_delivery_patch_proposal_enabled: bool = True
    software_delivery_patch_require_planning_approved: bool = True
    software_delivery_patch_require_active_branch: bool = True
    # FIX 125D — governed workspace code application (workspace tree only)
    software_delivery_workspace_apply_enabled: bool = True
    software_delivery_workspace_require_patch_approved: bool = True
    # FIX 125E — workspace verification (read-only checks + optional allowlisted test)
    software_delivery_workspace_verification_enabled: bool = True
    software_delivery_workspace_verification_require_applied: bool = True
    software_delivery_workspace_allow_allowlisted_test: bool = False
    # FIX 125F — PR draft artifact only (requires verification; no GitHub PR yet)
    software_delivery_pr_draft_enabled: bool = True
    software_delivery_pr_draft_require_verification: bool = True
    # FIX 125G — GitHub PR creation preflight (no push/PR yet; 125H/125I mutations)
    software_delivery_github_pr_preflight_enabled: bool = True
    software_delivery_github_pr_preflight_require_draft: bool = True
    # FIX 125H — governed GitHub feature-branch push (no PR/merge/deploy/main)
    software_delivery_github_branch_push_enabled: bool = True
    software_delivery_github_default_branch: str = "main"
    # FIX 125I — open GitHub PR after branch push (no merge/deploy/Railway)
    software_delivery_github_pr_open_enabled: bool = True
    # FIX 126 — Phase 2 software delivery loop frozen (125A–125I); do not disable without sign-off
    software_delivery_phase_2_frozen: bool = True
    # FIX 127 — bounded multi-agent advisory roles (no executor / no mutation)
    software_delivery_multi_agent_enabled: bool = True
    # FIX 128 — Mission Control cross-lane observability (read-only)
    mission_control_cross_lane_enabled: bool = True

    # Phase 9.8E.6 — governed web intelligence / research
    web_research_enabled: bool = False
    web_search_provider: str = "none"
    web_search_api_key: str = ""
    web_search_base_url: str = ""
    web_research_max_results: int = 5
    research_artifacts_dir: str = "data/research_artifacts"
    comparison_html_public_base_url: str = ""
    comparison_html_mirror_web_public: bool = False

    # Phase 9.8E.6.3 — Telegram typing + progress feedback
    telegram_typing_enabled: bool = True
    telegram_typing_interval_seconds: int = 4
    telegram_progress_message_enabled: bool = True
    telegram_progress_after_seconds: int = 8

    # Slack channel
    slack_enabled: bool = False
    slack_bot_token: str = ""
    slack_signing_secret: str = ""

    # Discord channel
    discord_enabled: bool = False
    discord_bot_token: str = ""
    discord_public_key: str = ""

    # WhatsApp channel — Meta WhatsApp Cloud API (token + webhook, vault-friendly).
    whatsapp_enabled: bool = False
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    # Meta app secret — when set, inbound webhooks must carry a valid
    # X-Hub-Signature-256 (HMAC-SHA256 of the raw body). Closes the open-webhook hole.
    whatsapp_app_secret: str = ""

    # Messenger channel — Meta Messenger Platform (Page token + webhook).
    messenger_enabled: bool = False
    messenger_page_access_token: str = ""
    messenger_verify_token: str = ""
    messenger_app_secret: str = ""

    # Autonomous execution plane (task registry, checkpoints, dispatcher)
    autonomous_execution_plane_enabled: bool = False
    operator_runtime_state_path: str = ""
    aethos_queue_limit: int = 500
    aethos_step_max_retries: int = 3
    aethos_plan_checkpoint_limit: int = 200

    # Vercel greenfield orchestration
    vercel_greenfield_execution_enabled: bool = False
    vercel_greenfield_phased_enablement: bool = True
    aws_readonly_inventory_enabled: bool = False
    cloud_readonly_inventory_enabled: bool = False
    kubernetes_vault_kubeconfig_enabled: bool = False

    # GitHub workflow dispatch (governed skill execute lane)
    github_workflow_dispatch_enabled: bool = False

    # Operator platform extensions
    llm_provider_routing_enabled: bool = True
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/auto"
    # §2 Multi-provider model keys — bring-your-own-model. Each provider's key may
    # come from .env (the operator) OR the MC vault (per-user). The *_model field is
    # the optional default model; the catalog also lists each provider's flagships.
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    mistral_api_key: str = ""
    mistral_model: str = "mistral-large-latest"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    xai_api_key: str = ""
    xai_model: str = "grok-2-latest"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"
    cohere_api_key: str = ""
    cohere_model: str = "command-r-plus"
    together_api_key: str = ""
    together_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    fireworks_api_key: str = ""
    fireworks_model: str = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    perplexity_api_key: str = ""
    perplexity_model: str = "sonar"
    local_llm_enabled: bool = False
    local_llm_base_url: str = ""
    local_llm_api_key: str = ""
    local_llm_default_model: str = "llama3.2"
    local_llm_models: str = ""
    # Drive the agent tool loop on the selected local model via the OpenAI-compatible
    # /v1/chat/completions tools API instead of silently swapping to a cloud model.
    # Default ON for transparency; falls back honestly (surfaced) only if the local
    # runtime can't do tool calling.
    local_tool_loop_enabled: bool = True
    # Drive the agent tool loop on the *selected* provider (OpenRouter / OpenAI-compatible
    # cloud) rather than swapping to Anthropic just because a key exists. Honors the
    # user's pick; an honest, surfaced fallback applies only when the provider truly
    # can't run tools. Default ON.
    multi_provider_tool_loop_enabled: bool = True
    # Bound the cross-provider failover chain so a multi-provider outage can't silently
    # cascade across many paid models. Counts total attempts (selected + fallbacks).
    model_failover_max_attempts: int = 3
    # Per-attempt LLM HTTP timeout — enough for real tool/large-context turns; §1 retry + §2 failover handle hangs.
    provider_llm_timeout_sec: float = 45.0
    # Short connect timeout so a stale pooled socket / blocked connect fails fast and we
    # retry on a FRESH connection instead of burning the whole read budget. Read/generation
    # still uses the full provider_llm_timeout_sec so a slow-but-working answer is never cut off.
    provider_llm_connect_timeout_sec: float = 10.0
    # Same-provider transient retries (timeout/connection/429/5xx) before cross-provider failover.
    # A valid key hitting a transient blip must recover on its own, so the default is forgiving.
    provider_llm_transient_retries: int = 4
    # Connection-level failures (stale keepalive socket, DNS/TLS blip, reset, pool timeout)
    # never reached the model and are always safe to retry — give them extra attempts on top
    # of the standard transient budget, with a near-instant first retry on a fresh socket.
    provider_llm_connection_error_extra_retries: int = 2
    provider_llm_retry_backoff_sec: float = 0.75
    # Drop pooled keepalive connections after this many idle seconds so we don't reuse a
    # socket the provider has already closed (the classic cause of "connection error" on a
    # valid key after the app has been idle).
    provider_llm_keepalive_expiry_sec: float = 20.0
    cron_governed_jobs_enabled: bool = False
    # User-defined scheduled tasks + inbound webhook triggers (governed delivery).
    proactive_automation_enabled: bool = False
    # PWA web push (proactive automation + job notifications when tab is closed).
    web_push_enabled: bool = False
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:ops@aethos.local"
    mcp_bridge_enabled: bool = True
    vector_memory_enabled: bool = True
    vector_memory_backend: str = "local"  # local | chroma
    chromadb_host: str = "localhost"
    chromadb_port: int = 8100

    # Runtime configuration store (UI-writable, precedence over .env). Holds
    # allowlisted user-settable, non-secret config so deployed end users can change
    # capabilities without .env access. Secrets stay in the vault; dangerous flags
    # stay operator-only. See aethos_core/runtime_config/.
    runtime_config_dir: str = "data/runtime_config"

    # Conversation summary memory (MEMORY.md "Conversation summary memory" layer):
    # a rolling, compressed per-session recap so "what did we discuss/do?" answers
    # from real conversation history. SQLite-backed, session-scoped, secrets redacted.
    conversation_memory_enabled: bool = True
    conversation_memory_dir: str = "data/conversation_memory"
    conversation_memory_max_turns: int = 80  # recent turns retained per session
    conversation_memory_max_summary_chars: int = 4000  # cap the rolling summary size

    # Phase 11.7.9 — Trigger.dev durable agent jobs substrate
    trigger_enabled: bool = False
    trigger_api_key: str = ""
    trigger_project_id: str = ""
    trigger_env: str = "dev"
    trigger_webhook_secret: str = ""
    trigger_default_timeout_seconds: int = 900
    trigger_max_retries: int = 3
    trigger_retry_backoff_seconds: int = 15
    trigger_stale_callback_minutes: int = 10
    trigger_orphaned_job_minutes: int = 30

    # Phase 9.9 — production deployment
    deployment_mode: str = "local"
    # Self-host / single-user mode. When true, AethOS runs as a personal control
    # plane: no multi-tenant beta gate, no auth wall, and the single local operator
    # IS the platform owner (full access to their own instance). Set SELF_HOST=true.
    self_host: bool = False
    # Shared Fernet key for credential vault encryption on hosted (set identically on api + worker).
    aethos_vault_key: str = ""
    worker_mode: str = "embedded"
    edge_runtime_enabled: bool = False
    hosted_cloud_enabled: bool = False

    # Operational environment label (development | staging | production | local)
    operational_environment: str = ""

    # Doctor / production hardening (development | staging | production | strict | relaxed)
    aethos_doctor_profile: str = ""
    aethos_operator_break_glass_acknowledged: bool = False

    # Cloudflare readonly inventory (optional token)
    cloudflare_api_token: str = ""

    # Email channel (SMTP)
    email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""
    sendgrid_api_key: str = ""

    # SMS / Voice (Twilio)
    sms_enabled: bool = False
    voice_enabled: bool = False
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_sms_from: str = ""
    twilio_voice_from: str = ""

    # Microsoft Teams (incoming webhook outbound + generic inbound webhook)
    teams_enabled: bool = False
    teams_webhook_url: str = ""

    # GCP / Azure credentials (readonly inventory)
    gcp_project_id: str = ""
    google_application_credentials: str = ""
    azure_subscription_id: str = ""
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""

    # Vector memory
    vector_memory_embedding_provider: str = "local"  # local | openrouter
    vector_memory_embedding_model: str = "text-embedding-3-small"

    # Vercel greenfield project creation
    vercel_greenfield_create_project_enabled: bool = True
    vercel_team_id: str = ""

    # Unified agentic-OS surfaces (AETHOS_OPERATOR_HANDOFF §3) — all network-facing
    # or mutating capabilities default OFF; each flag gates its capability at the
    # router/tool boundary. vector_memory_enabled / web_research_enabled already exist above.
    workspace_suite_enabled: bool = True
    workspace_suite_store_dir: str = "data/workspace_suite"
    channel_gateway_enabled: bool = False
    channel_dm_policy: str = "pairing"  # pairing | open
    channel_pairing_store_dir: str = "data/channel_pairing"
    channel_outbound_store_dir: str = "data/channel_outbound"
    outbound_send_execution_enabled: bool = False  # gate the actual send on approval
    voice_surface_enabled: bool = False
    # Voice & audio surface (local-first, all default OFF). voice_surface_enabled
    # is the master switch; the sub-flags gate mic capture / spoken replies / the
    # hands-free wake mode. TTS defaults to the browser's system voices; set
    # voice_tts_provider=elevenlabs (with a key) to upgrade. The ElevenLabs key is
    # read server-side only and never sent to the browser.
    voice_input_enabled: bool = False        # mic capture + speech-to-text
    voice_output_enabled: bool = False       # spoken replies (text-to-speech)
    voice_wake_enabled: bool = False         # hands-free talk mode + wake phrase
    voice_stt_provider: str = "browser"      # browser (Web Speech API) | whisper (OpenAI)
    voice_tts_provider: str = "system"       # system | elevenlabs
    elevenlabs_api_key: str = ""             # only used when voice_tts_provider=elevenlabs
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # default ElevenLabs voice
    elevenlabs_model_id: str = "eleven_turbo_v2_5"
    voice_wake_phrase: str = "hey aethos"
    canvas_surface_enabled: bool = True
    canvas_store_dir: str = "data/canvas"
    # §5 Skills registry — read-only operator playbooks from repo skills/. On by
    # default now that a real starter set ships; skill_recall returns matching
    # playbooks in Agent mode. Set false to hide them from chat recall.
    skills_registry_enabled: bool = True
    sandbox_nonmain_enabled: bool = True
    model_foundry_enabled: bool = True
    # Model Foundry convenience automation — opt-in, default OFF so today's safe
    # verify-only behavior is preserved. Approval of a specific serve item is the
    # consent gate for each of these actions when enabled.
    model_foundry_autostart_enabled: bool = False
    model_foundry_autodownload_enabled: bool = False
    # Stage 3 — login + first-run onboarding.
    # Onboarding is local-only personalization (collects name/hours/tone/goals);
    # default ON so fresh installs get the rapport wizard. Login is a
    # network-facing auth gate, so it is default OFF per the flag-gating rule.
    aethos_onboarding_enabled: bool = True
    aethos_login_enabled: bool = False
    aethos_login_passphrase: str = ""
    operator_persona_store_dir: str = "data/operator_persona"

    # Stage 4 — end-to-end provisioning orchestration (third-party connect plan).
    # Network-facing / mutating: default off; produces a governed multi-step plan.
    provisioning_orchestration_enabled: bool = False

    # §2 Enterprise authentication — server-side sessions + SSO (OIDC) + MFA (TOTP).
    # auth_enabled gates middleware enforcement on protected /api/v1 routes; default
    # OFF so local dev / existing single-operator deploys behave exactly as today.
    # Turn it on for any shared / multi-user deploy. Session signing key + TOTP
    # secrets live under the data dir (file-perms 0600), never in env.
    auth_enabled: bool = False
    auth_store_dir: str = "data/auth"
    auth_session_cookie: str = "aethos_session"
    auth_session_idle_timeout_sec: int = 1800        # 30 min idle window
    auth_session_absolute_timeout_sec: int = 43200   # 12 h hard cap
    auth_cookie_secure: bool = True                  # set False only for plain-http localhost
    auth_bootstrap_admin_email: str = ""             # first-run admin (password set via /bootstrap)
    # Comma-separated owner emails — set only in Railway Variables (PLATFORM_OWNER_EMAILS).
    # Computed per request; never stored on user records or grantable via UI/API.
    platform_owner_emails: str = ""
    # Stripe billing webhook seam — default off; manual entitlements via Owner console.
    billing_enabled: bool = False
    # Stripe (real billing). Empty ⇒ checkout/webhook return billing_not_configured.
    # No SDK dependency: checkout via Stripe REST, webhook via manual HMAC verification.
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""  # the recurring price the Checkout session subscribes to
    stripe_trial_days: int = 0  # optional free-trial days on the subscription
    # Social connectors: tokens live in the vault (provider = platform name). Mastodon needs the
    # instance base URL; other platforms are identified by their token alone.
    mastodon_base_url: str = ""
    # Client/server build version + minimum supported client (forced refresh gate).
    # Empty ⇒ API uses RAILWAY_GIT_COMMIT_SHA on deploy; set APP_VERSION to override.
    app_version: str = ""
    # Only when set — hard-blocks clients below this (Update required screen).
    min_supported_app_version: str = ""
    auth_login_max_attempts: int = 5                 # per-account brute-force lockout threshold
    auth_login_lockout_sec: int = 900                # lockout window after threshold
    # SSO via OIDC (Okta / Microsoft Entra / Google Workspace). Back-channel
    # authorization-code flow with PKCE; client secret stays server-side.
    sso_enabled: bool = False
    oidc_issuer: str = ""                             # e.g. https://login.example.com
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_redirect_url: str = ""                       # https://aethos.example.com/api/v1/aethos-identity/sso/callback
    oidc_scopes: str = "openid email profile"
    oidc_allowed_domains: str = ""                    # comma-separated email domains; empty = any verified
    # MFA / TOTP for local accounts (RFC 6238). Enforced at login for users who
    # have enrolled; admins can require enrollment via auth_mfa_required.
    mfa_enabled: bool = False
    mfa_required: bool = False
    mfa_issuer_label: str = "AethOS"
    # Self-service local registration (email + password). OFF by default: on a
    # single-operator deploy you don't want open signup. Turn ON for an
    # email+password beta so each user creates their own account from the UI.
    # New accounts always get the "operator" role only — never admin/approver.
    auth_self_signup_enabled: bool = False
    auth_verification_ttl_sec: int = 86400
    auth_verification_resend_cooldown_sec: int = 120
    # Public web app URL for emailed links (signup verify, etc.). Include any
    # path prefix — e.g. https://pilotmain.com/aethos. On hosted deploys, set this
    # so verification emails never point at localhost or the API origin.
    public_app_base_url: str = ""

    # Multi-tenancy (operator-only; see MULTI_TENANT_PLAN.md). OFF by default ⇒
    # byte-for-byte single-tenant behavior. When ON: auth is REQUIRED (the auth
    # middleware enforces sessions even if auth_enabled is left off — fail closed),
    # each request resolves a per-user tenant, and detached work (durable jobs,
    # arbiter sessions) is stamped with the owning tenant_id at creation so it
    # never resolves another tenant's resources. Resolvers become tenant-aware in
    # later phases; this flag gates the whole feature.
    multi_tenant_enabled: bool = False
    # Per-tenant abuse ceilings (Correction 4). The shared instance's compute is
    # paid by the operator even with BYOK, and the arbiter fans out to many models
    # per turn, so a single tenant could run up cost / DoS the box. This limit
    # applies per non-operator tenant only when MULTI_TENANT_ENABLED; the operator
    # (default tenant) is exempt. 0 disables it. Per-request throttling is already
    # handled per-session by the §4 HTTP rate limiter.
    tenant_arbiter_runs_per_hour: int = 60
    # Per-tenant daily LLM token ceiling (input+output). 0 = unlimited. Applies to
    # non-operator tenants only when MULTI_TENANT_ENABLED.
    tenant_llm_tokens_per_day: int = 0

    # §3 Unified tamper-evident audit ledger — one append-only, hash-chained log
    # of privileged actions (login, vault r/w, preflight, approval, mutation
    # execute, channel send, agent spawn). On by default: it is read-only spine
    # over existing domain logs and never blocks the action it records.
    audit_ledger_enabled: bool = True
    audit_ledger_dir: str = "data/audit"

    # §4 API rate limiting & abuse protection — per-identity (session) + per-IP
    # sliding-window limits at the middleware layer, plus a request body size cap.
    # On by default with generous limits; auth/mutation/chat get tighter buckets.
    # Loopback (127.0.0.1/::1) is exempt so local single-operator use is unaffected.
    rate_limit_enabled: bool = True
    rate_limit_window_sec: int = 60
    rate_limit_default_per_min: int = 240
    rate_limit_auth_per_min: int = 10        # brute-force resistance on login/SSO/MFA
    rate_limit_mutation_per_min: int = 30
    rate_limit_chat_per_min: int = 90
    rate_limit_exempt_loopback: bool = True
    max_request_bytes: int = 10_485_760      # 10 MiB hard cap on request bodies

    # §5 Transport security headers — applied to every API response. On by
    # default. HSTS is honored only over HTTPS (ignored on plain http), so it is
    # safe to leave enabled; a TLS-terminating reverse proxy is required for any
    # non-localhost deploy (see SECURITY.md). CSP is relaxed on the docs routes
    # so Swagger/Redoc keep working; override security_headers_csp to tighten.
    security_headers_enabled: bool = True
    security_headers_hsts_enabled: bool = True
    security_headers_hsts_max_age: int = 63072000   # 2 years
    security_headers_csp: str = (
        "default-src 'self'; img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self'; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    security_headers_referrer_policy: str = "strict-origin-when-cross-origin"
    security_headers_permissions_policy: str = "geolocation=(), camera=(), microphone=(), payment=()"

    # §8 Observability export — OpenTelemetry traces/metrics, structured JSON logs,
    # an error-tracking sink, and SLO thresholds. All optional/default-off so no
    # new hard dependency is required; OTel/Sentry activate only when their libs
    # are installed and the corresponding flag is set.
    otel_enabled: bool = False
    otel_service_name: str = "aethos"
    otel_exporter_otlp_endpoint: str = ""    # e.g. http://otel-collector:4318
    log_format: str = "text"                 # text | json (structured, secret-redacted)
    error_tracking_enabled: bool = False
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.0
    # SLO targets + alert thresholds.
    slo_chat_latency_ms: float = 8000.0      # avg chat turn latency budget
    slo_mutation_success_rate: float = 0.95  # successful mutation executions / total

    # §9 External KMS / secret-manager option — envelope-encrypt the vault's data
    # encryption key (DEK) with an external Key Encryption Key (KEK). Default ""
    # keeps the local encrypted-file vault unchanged. Supported: aws | gcp | vault.
    kms_backend: str = ""                     # "" (local) | aws | gcp | vault
    aws_kms_key_id: str = ""                   # arn or key-id / alias
    aws_region: str = ""
    gcp_kms_key_name: str = ""                 # projects/.../cryptoKeys/...
    vault_kms_addr: str = ""                   # https://vault.example.com:8200
    vault_kms_token: str = ""
    vault_kms_transit_key: str = "aethos"      # transit key name

    # §10 Data governance — retention, PII redaction, backup/restore.
    # Retention is opt-in per category (0 days = keep forever) to avoid accidental
    # data loss. Audit retention archives old entries (never silently deletes) and
    # re-chains the active ledger, preserving tamper-evidence. PII redaction in
    # logs is on by default.
    retention_enabled: bool = False
    retention_chat_days: int = 0
    retention_jobs_days: int = 0
    retention_artifacts_days: int = 0
    retention_audit_days: int = 0
    pii_redaction_enabled: bool = True
    backup_dir: str = "data/backups"

    # ── Arbiter: multi-model parallel dispatch + critique consensus ──────────
    # On with batteries included (uses user's connected model keys). All arbiter code
    # is isolated in aethos_core/arbiter/; existing chat, provider, agent, and job
    # systems are untouched.
    arbiter_enabled: bool = True
    # Comma-separated "provider:model_id" pairs for the arbiter pool. Example:
    # "anthropic:claude-opus-4-6,openrouter:openai/gpt-4.1,local:llama3.2".
    # At most ARBITER_MAX_MODELS entries are used; extras are silently ignored.
    arbiter_model_pool: str = ""
    # Fraction of eligible critics that must recommend the same response to
    # declare consensus. Range 0.0–1.0. Fortune 500 recommendation: 0.7+.
    arbiter_consensus_threshold: float = 0.6
    # Max critique rounds after the initial parallel dispatch (round 0 = collect).
    arbiter_max_rounds: int = 1
    # Debate mode: hard cap on revise→re-critique rounds a caller may request.
    # Each round costs one revise call per model + one critique pass, so this bounds
    # fan-out cost for tenants paying with their own keys. 0 disables debate.
    arbiter_max_debate_rounds: int = 3
    # Hard cap on pool size (cost + latency control).
    arbiter_max_models: int = 8
    # Wall-clock budget for the full arbiter session (all rounds combined).
    arbiter_timeout_sec: float = 180.0
    # True → critique is blind (critic does not see which model wrote a response),
    # preventing prestige bias. False → critic sees model labels (meta-critique).
    arbiter_blind_critique: bool = True
    # Persist full model responses in the artifact payload (True) or summaries
    # only (False) for high-sensitivity prompts.
    arbiter_persist_full_responses: bool = True

    # ── Daily Digest agent (Feature 2) ──────────────────────────────────────
    # Scheduled morning briefing (deploys, jobs, approvals, monitors, social).
    digest_enabled: bool = False
    # Local-time hour (0–23) to deliver the daily digest (scheduler ticks hourly).
    digest_hour: int = 8
    # Polish the digest into prose via the LLM (costs tokens). Off = deterministic bullets.
    digest_llm: bool = False
    # Optional Telegram chat id to push the digest to (requires a resolvable bot token).
    digest_telegram_chat: str = ""

    # ── Tool/skill relevance routing (Feature 3) ────────────────────────────
    # Trim the model-facing tool list to the most relevant per query (cheaper, sharper,
    # avoids context rot). Off by default → unchanged behaviour; on → trims to the top
    # `tool_relevance_max` tools + a small always-on core when the catalog is larger.
    tool_relevance_enabled: bool = False
    tool_relevance_max: int = 14

    # ── Cost-aware model routing (Feature 4) ────────────────────────────────
    # Route SIMPLE turns to a cheaper model when the user hasn't picked a model
    # explicitly; complex turns + explicit selections always use the full model.
    # Off by default; needs cost_router_cheap_model to name a configured catalog model.
    cost_aware_routing_enabled: bool = False
    cost_router_cheap_model: str = ""

    # ── Self-organizing memory (Feature 5) ──────────────────────────────────
    # Compress a topic's memories into a digest via the LLM (off → deterministic join).
    memory_compression_llm: bool = False

    # ── Skill optimization from traces (Feature 6) ──────────────────────────
    # Polish skill-improvement suggestions into prose via the LLM (off → deterministic).
    skill_optimization_llm: bool = False

    # ── Proactive suggestions (Feature 8) ───────────────────────────────────
    # Surface "you might want to…" proposals from existing signals. Read-only/gated —
    # never auto-executes. Off by default.
    proactive_suggestions_enabled: bool = False

    @model_validator(mode="after")
    def _apply_batteries_included_profile(self) -> Self:
        if self.aethos_batteries_included:
            return self
        for field_name in _BATTERIES_INCLUDED_FLAGS:
            object.__setattr__(self, field_name, False)
        return self

    @model_validator(mode="after")
    def _apply_self_host_profile(self) -> Self:
        """Self-host is single-user by construction: the multi-tenant beta gate and
        the auth wall (both built for the hosted SaaS) are forced off so a local
        operator is never locked out of their own instance. Owner rights are granted
        in rbac.is_platform_owner."""
        if self.self_host:
            object.__setattr__(self, "multi_tenant_enabled", False)
            object.__setattr__(self, "auth_enabled", False)
        return self


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    # Apply UI-set runtime overrides (store -> .env -> default) onto the singleton so
    # existing get_settings() reads honor user changes without per-call-site edits.
    # Allowlisted, non-secret keys only; never weakens governance (see runtime_config).
    try:
        from aethos_core.runtime_config.effective_settings import apply_runtime_overrides

        apply_runtime_overrides(s)
    except Exception:
        pass
    vercel_cli = shutil.which("vercel") is not None
    from aethos_core.runtime.authority import authority

    # Env key only at bootstrap — vault keys resolve per-request without re-entering
    # get_settings() (anthropic_configured() would recurse during singleton init).
    provider_available = bool(
        s.use_real_llm
        and s.active_provider == "anthropic"
        and s.anthropic_api_key.strip()
    )
    authority.configure_capabilities(
        browser_automation=s.browser_automation_enabled,
        host_executor=s.host_executor_enabled,
        vercel_cli=vercel_cli,
        provider_available=provider_available,
    )
    authority.record_health_ok()
    if s.web_api_token:
        authority.record_auth_valid()
    else:
        authority.record_auth_valid()  # dev: open local chat
    from aethos_core.research.research_config import validate_research_config_at_startup

    validate_research_config_at_startup(s)
    return s
