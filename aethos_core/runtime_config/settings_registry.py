# SPDX-License-Identifier: Apache-2.0
"""Allowlist of user-settable runtime settings (the §3 guardrail boundary).

Only keys defined here may be written from the UI via the runtime config store.
Secrets are NEVER here (they go to the vault); dangerous/governance flags are NEVER
here (operator/.env only). Every spec maps a public KEY to a real Settings field so
the resolver can type values and apply overrides to the live settings object.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SettingSpec:
    key: str  # public, env-style (UPPER_SNAKE) — used by the API + UI
    attr: str  # the aethos_core.config.Settings attribute (lower_snake)
    kind: str  # "bool" | "str" | "enum" | "float" | "int"
    group: str  # Features | Models | Channels | Services
    label: str
    description: str = ""
    options: tuple[str, ...] = field(default_factory=tuple)  # for kind == "enum"
    restart_required: bool = False


# ── User-settable settings (the only writable keys) ─────────────────────────
USER_SETTABLE_SETTINGS: tuple[SettingSpec, ...] = (
    # Features ----------------------------------------------------------------
    SettingSpec("USE_REAL_LLM", "use_real_llm", "bool", "Features", "LLM reasoning",
                "Use a connected model for reasoning instead of deterministic-only replies."),
    SettingSpec("ARBITER_ENABLED", "arbiter_enabled", "bool", "Features", "Multi-model arbiter",
                "Enable the multi-model arbiter (parallel dispatch, critique, consensus)."),
    SettingSpec("WORKSPACE_SUITE_ENABLED", "workspace_suite_enabled", "bool", "Features", "Workspace suite",
                "Research, compare, documents, notes, email triage, and calendar tools."),
    SettingSpec("CANVAS_SURFACE_ENABLED", "canvas_surface_enabled", "bool", "Features", "Live Canvas",
                "Render read-only structured views to the Live Canvas surface."),
    SettingSpec("MODEL_FOUNDRY_ENABLED", "model_foundry_enabled", "bool", "Features", "Model Foundry",
                "Scan hardware and recommend/serve local open models (governed)."),
    SettingSpec("WEB_RESEARCH_ENABLED", "web_research_enabled", "bool", "Features", "Web research",
                "Allow multi-step deep research from public web sources."),
    SettingSpec("BROWSER_AUTOMATION_ENABLED", "browser_automation_enabled", "bool", "Features",
                "Governed browser observation", "Read-only governed browser observation lane."),
    SettingSpec("VECTOR_MEMORY_ENABLED", "vector_memory_enabled", "bool", "Features", "Long-term memory",
                "Embed memory for cross-session recall (semantic vector store)."),
    SettingSpec("CONVERSATION_MEMORY_ENABLED", "conversation_memory_enabled", "bool", "Features",
                "Conversation memory", "Keep a rolling per-session recap of what was discussed/done."),
    SettingSpec("LIVE_PROGRESS_ENABLED", "live_progress_enabled", "bool", "Features", "Live progress narration",
                "Stream human-readable step/thought events during tool runs."),
    SettingSpec("MCP_BRIDGE_ENABLED", "mcp_bridge_enabled", "bool", "Features", "MCP bridge",
                "Expose the Model Context Protocol bridge."),
    SettingSpec("CRON_GOVERNED_JOBS_ENABLED", "cron_governed_jobs_enabled", "bool", "Features",
                "Scheduled jobs", "Record cron-style scheduled tasks (governed; never auto-executes)."),
    SettingSpec("PROACTIVE_AUTOMATION_ENABLED", "proactive_automation_enabled", "bool", "Features",
                "Proactive automation", "User-defined schedules and webhook triggers with governed delivery."),
    SettingSpec("VOICE_ENABLED", "voice_enabled", "bool", "Features", "Voice (Twilio)",
                "Enable the Twilio voice channel (distinct from the web voice surface)."),
    SettingSpec("VOICE_SURFACE_ENABLED", "voice_surface_enabled", "bool", "Features", "Voice surface",
                "Master switch for web talk-to-AethOS (mic + spoken replies)."),
    SettingSpec("VOICE_INPUT_ENABLED", "voice_input_enabled", "bool", "Features", "Voice input",
                "Allow microphone capture and speech-to-text."),
    SettingSpec("VOICE_OUTPUT_ENABLED", "voice_output_enabled", "bool", "Features", "Voice output",
                "Speak AethOS replies aloud (system TTS or ElevenLabs)."),
    SettingSpec("VOICE_WAKE_ENABLED", "voice_wake_enabled", "bool", "Features", "Voice wake mode",
                "Hands-free talk mode with a wake phrase."),
    SettingSpec("VOICE_STT_PROVIDER", "voice_stt_provider", "enum", "Features", "Speech-to-text",
                "browser (Web Speech API) or whisper (OpenAI Whisper, server-side)."),
    SettingSpec("VOICE_TTS_PROVIDER", "voice_tts_provider", "enum", "Features", "Text-to-speech",
                "system (browser voices) or elevenlabs (premium, server-side)."),
    SettingSpec("WEB_PUSH_ENABLED", "web_push_enabled", "bool", "Features", "Web push",
                "Send push notifications for proactive automations when the tab is closed."),
    # Channels ----------------------------------------------------------------
    SettingSpec("CHANNEL_GATEWAY_ENABLED", "channel_gateway_enabled", "bool", "Channels", "Outbound channel gateway",
                "Allow governed outbound messages (approval + allowlist still required)."),
    SettingSpec("TELEGRAM_ENABLED", "telegram_enabled", "bool", "Channels", "Telegram",
                "Enable the Telegram channel (token is stored in the vault)."),
    SettingSpec("SLACK_ENABLED", "slack_enabled", "bool", "Channels", "Slack",
                "Enable the Slack channel (credentials are stored in the vault)."),
    SettingSpec("DISCORD_ENABLED", "discord_enabled", "bool", "Channels", "Discord",
                "Enable the Discord channel (credentials are stored in the vault)."),
    SettingSpec("WHATSAPP_ENABLED", "whatsapp_enabled", "bool", "Channels", "WhatsApp",
                "Enable the WhatsApp Cloud channel (credentials are stored in the vault)."),
    SettingSpec("MESSENGER_ENABLED", "messenger_enabled", "bool", "Channels", "Messenger",
                "Enable the Messenger channel (credentials are stored in the vault)."),
    # Models ------------------------------------------------------------------
    SettingSpec("ARBITER_MODEL_POOL", "arbiter_model_pool", "str", "Models", "Arbiter model pool",
                "Comma list of provider:model the arbiter dispatches to. Empty = use connected models."),
    SettingSpec("ARBITER_BLIND_CRITIQUE", "arbiter_blind_critique", "bool", "Models", "Blind critique",
                "Critics score responses without seeing which model wrote them."),
    SettingSpec("ACTIVE_PROVIDER", "active_provider", "str", "Models", "Default provider",
                "Default model provider for chat when no per-session override is set."),
    # Services ----------------------------------------------------------------
    SettingSpec("WEB_SEARCH_PROVIDER", "web_search_provider", "enum", "Services", "Web search provider",
                "Search backend for web research.", options=("none", "tavily", "serper", "brave", "bing")),
)

_BY_KEY = {spec.key: spec for spec in USER_SETTABLE_SETTINGS}
_BY_ATTR = {spec.attr: spec for spec in USER_SETTABLE_SETTINGS}


# ── Operator-only / dangerous keys — explicitly NEVER user-settable ─────────
# Kept for defense-in-depth + clear error messages; they are also simply absent
# from USER_SETTABLE_SETTINGS so the resolver rejects them regardless.
OPERATOR_ONLY_KEYS: frozenset[str] = frozenset(
    {
        "AETHOS_SOLO_EXECUTION_MODE",
        "AETHOS_SOLO_AUTO_APPROVE",
        "AETHOS_SOLO_AUTO_APPROVE_READONLY",
        "AETHOS_SOLO_AUTO_APPROVE_MUTATION",
        "AUTONOMOUS_EXECUTION_ENABLED",
        "HOST_EXECUTOR_ENABLED",
        "SANDBOX_NONMAIN_ENABLED",
        "AUDIT_LEDGER_ENABLED",
        "MUTATION_EXECUTION_ENABLED",
        "MUTATION_T3_PRODUCTION_ENABLED",
    }
)


def normalize_key(key: str) -> str:
    return (key or "").strip().upper()


def is_dangerous_key(key: str) -> bool:
    k = normalize_key(key)
    if k in OPERATOR_ONLY_KEYS:
        return True
    return any(
        token in k
        for token in ("SOLO_", "AUTO_APPROVE", "AUTONOMOUS", "PRESENTATION_BYPASS", "MUTATION_", "SANDBOX")
    )


def looks_like_secret_key(key: str) -> bool:
    k = normalize_key(key)
    return any(token in k for token in ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "AUTHTOKEN"))


def get_setting_spec(key: str) -> SettingSpec | None:
    return _BY_KEY.get(normalize_key(key))


def get_setting_spec_by_attr(attr: str) -> SettingSpec | None:
    return _BY_ATTR.get((attr or "").strip().lower())


def list_setting_specs() -> tuple[SettingSpec, ...]:
    return USER_SETTABLE_SETTINGS
