# SPDX-License-Identifier: Apache-2.0
"""Project-direction and capability templates — no provider required."""

from __future__ import annotations

import re

from aethos_core.runtime.authority import authority

# --- detection (mirrored in lanes.py) ---

_ANTHROPIC_MISSING_RX = re.compile(
    r"\b(what happens if|if)\b.*\b(anthropic|provider|llm|real llm)\b.*"
    r"\b(not configured|missing|offline|unavailable|disabled)\b",
    re.I,
)
_RESTART_RX = re.compile(
    r"\b(can you|could you)\b.*\brestart\b.*\baethos\b|\brestart aethos\b",
    re.I,
)
_BROWSER_AUTO_RX = re.compile(
    r"\b(can you|could you)\b.*\b(browser automation|use browser automation)\b|"
    r"\bbrowser automation\b",
    re.I,
)
_CHANNELS_RX = re.compile(
    r"\b(what channels|channels should|which channels)\b.*\b(support|add|later)\b|"
    r"\bchannels should aethos support\b",
    re.I,
)
def is_canvas_render_request(text: str) -> bool:
    """True when the prompt explicitly asks AethOS to render to the Canvas surface.

    Single source of truth: delegate to front_door_intent so every router (primary-intent
    gate, provider preflight, railway readonly) agrees. The previous local regex required the
    verb within 40 chars of "canvas" and so missed long prompts ending in "… on the canvas",
    which then leaked into deploy/provider lanes.
    """
    from aethos_core.chat.front_door_intent import is_canvas_render_request as _canonical

    return _canonical(text)


_MISSION_CONTROL_RX = re.compile(
    r"\b(how should|what is|how will)\b.*\bmission control\b|"
    r"\bmission control\b.*\b(work|behave|function|do)\b",
    re.I,
)
_DIFFERENT_RX = re.compile(
    r"\b(what makes|how is)\b.*\baethos\b.*\b(different|unique)\b|"
    r"^\s*why\s+aethos\??\s*$|"
    r"\bwhy aethos\b|"
    r"\b\w+\s+makes\b.*\baethos\b.*\bdifferent\b",
    re.I,
)
_PROJECT_SUMMARY_RX = re.compile(
    r"\b(summarize|summary of|summarise)\b.*\b(project direction|current direction|current project)\b|"
    r"\bsummarize the current project direction\b",
    re.I,
)
_TEST_CHECKLIST_RX = re.compile(
    r"\b(test checklist|write a simple test checklist|simple test checklist)\b",
    re.I,
)
_NEXT_STEPS_RX = re.compile(
    r"\b(what should we do next|what should i do next|what's next|what are the next steps)\b|"
    r"^\s*what should we do next\??\s*$",
    re.I,
)
_ARCHITECTURE_RX = re.compile(
    r"\b(explain|describe)\b.*\baethos\b.*\barchitecture\b|\baethos architecture\b",
    re.I,
)
_BUILD_FIRST_RX = re.compile(
    r"\b(what should|what)\b.*\baethos\b.*\bbuild first\b",
    re.I,
)
_MVP_ROADMAP_RX = re.compile(
    r"\b(draft|create|write)\b.*\bmvp roadmap\b|\bmvp roadmap\b",
    re.I,
)
_RELIABILITY_RX = re.compile(
    r"\b(how should|stay|keep)\b.*\baethos\b.*\b(fast|reliable)\b|"
    r"\bfast and reliable\b|stay fast and reliable\b",
    re.I,
)

GENERIC_FALLBACK_MARKER = "Generative mode (provider not configured)"


def provider_setup_footer() -> str:
    return (
        "**To enable full reasoning:**\n"
        "1. Add `ANTHROPIC_API_KEY` to `.env`\n"
        "2. Set `USE_REAL_LLM=true`\n"
        "3. Restart the API"
    )


def anthropic_missing_reply() -> str:
    from aethos_core.config import get_settings
    from aethos_core.provider.completion import provider_configured

    s = get_settings()
    configured = provider_configured()
    lines = [
        "**When Anthropic is not configured**",
        "",
        "AethOS still answers capability, setup, and project-direction questions "
        "through the **deterministic lane** — no provider required.",
        "",
        f"- `USE_REAL_LLM`: **{s.use_real_llm}**",
        f"- Active provider: **{s.active_provider}**",
        f"- Provider ready: **{'yes' if configured else 'no'}**",
        f"- Model (when enabled): **{s.anthropic_model}**",
        "",
        "Open-ended reasoning uses template answers until the provider is enabled. "
        "Chat stays fast and stable either way.",
        "",
        provider_setup_footer(),
    ]
    return "\n".join(lines)


def restart_capability_reply(session_id: str = "default") -> tuple[str, str, dict[str, str]]:
    from aethos_core.chat.action_prompts import propose_restart_reply

    return propose_restart_reply(session_id)


def browser_automation_capability_reply() -> str:
    caps = authority.capabilities
    if caps["browser_automation_enabled"]:
        return (
            "**Browser automation**\n\n"
            "Yes — browser automation is **enabled**. I can open allowed sites after your "
            "**explicit approval** per task. I will not reuse stored credentials without consent."
        )
    return (
        "**Browser automation**\n\n"
        "Not yet — browser automation is **off** in this deployment.\n\n"
        "To enable: set `BROWSER_AUTOMATION_ENABLED=true` in `.env`, restart the API, "
        "then ask again. Public status pages work without login."
    )


def channel_roadmap_reply() -> str:
    return (
        "**Channel roadmap (later phases)**\n\n"
        "Phase 1 focus is **web chat** — fast, reliable, independent of Mission Control.\n\n"
        "Planned channels (one at a time, after stability gates):\n"
        "1. **Web** — primary MVP (current)\n"
        "2. **Telegram** — operator notifications and quick commands\n"
        "3. **API / SDK** — programmatic access for automations\n"
        "4. **Additional chat surfaces** — only after each prior channel is stable\n\n"
        "Each channel gets the same chat lane; Mission Control stays observational."
    )


def mission_control_plan_reply() -> str:
    return (
        "**Mission Control (Phase 2 — observational only)**\n\n"
        "Mission Control is a **read-only** operator view. It must never own chat state "
        "or block sends.\n\n"
        "**Initial tabs:** Runtime · Jobs · Settings\n\n"
        "**It may:** show runtime status, list jobs, display settings.\n"
        "**It must not:** inject errors into chat, require websockets for chat, or degrade the send path.\n\n"
        "Chat remains primary. Mission Control subscribes to runtime authority — it does not drive chat."
    )


def differentiation_reply() -> str:
    return (
        "**What makes AethOS different**\n\n"
        "AethOS is built **chat-first**: fast deterministic answers, optional provider depth, "
        "and Mission Control that stays observational — never entangled with send state.\n\n"
        "- **Reliable by default** — every turn completes; no panel-degraded chat copy\n"
        "- **Useful without a provider** — capabilities and project direction work offline\n"
        "- **Gradual power** — agentic features only after stability gates pass\n\n"
        "Simple, confident operator assistant — not a fragile demo shell."
    )


def project_direction_summary_reply() -> str:
    return (
        "**Current project direction**\n\n"
        "AethOS is a clean rebuild focused on **simple, reliable chat first**.\n\n"
        "**Now (Phase 1):** deterministic + provider lanes, lightweight web UI, 20-turn gate.\n"
        "**Next (Phase 2):** minimal observational Mission Control — no chat coupling.\n"
        "**Later:** runtime actions, orchestration, browser automation, channels — one feature at a time.\n\n"
        "Principle: *build → test → stabilize → continue*. No stacking unfinished systems."
    )


def test_checklist_reply() -> str:
    return (
        "**Simple test checklist (Phase 1)**\n\n"
        "- [ ] API health returns `chat_ready: true`\n"
        "- [ ] 20-turn API smoke passes\n"
        "- [ ] 20-turn browser smoke passes (one session, no refresh)\n"
        "- [ ] Deterministic prompts never show provider-not-configured boilerplate\n"
        "- [ ] Messages persist in sessionStorage across navigation\n"
        "- [ ] Send button clears after each turn\n"
        "- [ ] No `[object Object]`, `AbortError`, or Panel degraded in chat\n"
        "- [ ] Provider optional — useful answers without Anthropic\n\n"
        "After all pass → Phase 2 Mission Control."
    )


def next_steps_reply() -> str:
    return (
        "**What we should do next**\n\n"
        "**Phase 1.1 is passing.** Finish the browser smoke gate (prompts 17 and 20 confirmed), "
        "then move on.\n\n"
        "**Next step:** Start **Phase 2** — minimal observational Mission Control "
        "(Runtime, Jobs, Settings). Mission Control must not affect chat.\n\n"
        "Do not add advanced features, websockets, or orchestration until Phase 2 is stable."
    )


def architecture_summary_reply() -> str:
    return (
        "**AethOS architecture (MVP)**\n\n"
        "```\n"
        "Runtime Authority (Layer 1)\n"
        "    ├── Chat Lane (Layer 2) — PRIMARY\n"
        "    │     Lane A: deterministic (instant)\n"
        "    │     Lane B: provider (when configured)\n"
        "    └── Mission Control (Layer 3) — observational, later\n"
        "```\n\n"
        "**Key modules:** `aethos_core/runtime/authority.py`, `chat/lanes.py`, `chat/handlers.py`, "
        "`chat/service.py`, `api/routes/chat.py`, `web/components/ChatShell.tsx`.\n\n"
        "**Isolation rule:** chat errors never use Mission Control copy; MC failures never block send."
    )


def mvp_roadmap_reply() -> str:
    return (
        "**MVP roadmap**\n\n"
        "**Phase 1 — Chat MVP** ✓ (stabilizing)\n"
        "- Health, deterministic chat, provider route, web shell, reliability gate\n\n"
        "**Phase 1.1 — Deterministic intelligence** (current)\n"
        "- Project-direction templates, capability coverage, better fallback\n\n"
        "**Phase 2 — Mission Control**\n"
        "- Observational tabs: Runtime, Jobs, Settings\n\n"
        "**Phase 3 — Runtime actions**\n"
        "- Approved restarts, browser automation toggles, CLI checks\n\n"
        "**Phase 4 — Agentic OS**\n"
        "- Orchestration, subagents, memory — one feature at a time with gates"
    )


def reliability_plan_reply() -> str:
    return (
        "**Fast and reliable by design**\n\n"
        "1. **Deterministic first** — capability and project questions skip the provider\n"
        "2. **Single send path** — one fetch per turn; no websocket for chat in MVP\n"
        "3. **Session persistence** — messages cached in sessionStorage\n"
        "4. **Health isolation** — panel/MC state never degrades chat copy\n"
        "5. **Gates before features** — 20-turn smoke before each new layer\n"
        "6. **Small diffs** — fix one failing prompt, rerun smoke, continue\n\n"
        "Speed comes from skipping unnecessary work; reliability comes from finishing every turn."
    )


def match_project_template(
    text: str, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    """Return (reply, intent, meta) for project/capability templates."""
    raw = (text or "").strip()
    if not raw:
        return None
    from aethos_core.world_model.investigation_strategy_router import (
        has_investigation_continuity,
        is_investigation_strategy_question,
    )

    if is_investigation_strategy_question(raw) and has_investigation_continuity(text=raw, session_id=session_id):
        return None
    if _ANTHROPIC_MISSING_RX.search(raw):
        return anthropic_missing_reply(), "runtime_config_query", {}
    if _RESTART_RX.search(raw):
        from aethos_core.chat.local_system_guidance import (
            is_local_aethos_api_restart_intent,
            route_local_system_guidance,
        )

        if is_local_aethos_api_restart_intent(raw):
            guided = route_local_system_guidance(raw, session_id=session_id)
            if guided is not None:
                return guided
        return restart_capability_reply(session_id)
    if _BROWSER_AUTO_RX.search(raw):
        return browser_automation_capability_reply(), "capability_question", {}
    if _CHANNELS_RX.search(raw):
        return channel_roadmap_reply(), "planning", {}
    if _MISSION_CONTROL_RX.search(raw):
        return mission_control_plan_reply(), "planning", {}
    if _DIFFERENT_RX.search(raw):
        return differentiation_reply(), "planning", {}
    if _PROJECT_SUMMARY_RX.search(raw):
        return project_direction_summary_reply(), "planning", {}
    if _TEST_CHECKLIST_RX.search(raw):
        return test_checklist_reply(), "planning", {}
    if _NEXT_STEPS_RX.search(raw):
        from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
            workflow_discovery_preemption_blocks_route,
        )

        if workflow_discovery_preemption_blocks_route(raw, session_id=session_id):
            return None
        return next_steps_reply(), "planning", {}
    if _ARCHITECTURE_RX.search(raw):
        return architecture_summary_reply(), "planning", {}
    if _BUILD_FIRST_RX.search(raw):
        return build_first_reply(), "planning", {}
    if _MVP_ROADMAP_RX.search(raw):
        return mvp_roadmap_reply(), "planning", {}
    if _RELIABILITY_RX.search(raw):
        return reliability_plan_reply(), "planning", {}
    return None


def build_first_reply() -> str:
    return (
        "**What AethOS should build first**\n\n"
        "1. **Reliable chat** — deterministic lane + provider route + session persistence\n"
        "2. **Runtime authority** — one health/capability snapshot\n"
        "3. **Observational Mission Control** — after chat gate passes\n"
        "4. **Approved runtime actions** — restart, CLI, browser — through authority only\n\n"
        "Nothing else until the previous layer is stable and tested."
    )


def try_partial_template(user_text: str, *, session_id: str = "default") -> str | None:
    """Best-effort template for provider-off generative fallback."""
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        workflow_discovery_preemption_blocks_route,
    )
    from aethos_core.world_model.investigation_strategy_router import (
        has_investigation_continuity,
        is_investigation_strategy_question,
    )

    if workflow_discovery_preemption_blocks_route(user_text, session_id=session_id):
        return None

    if is_investigation_strategy_question(user_text) and has_investigation_continuity(
        text=user_text,
        session_id=session_id,
    ):
        return None
    matched = match_project_template(user_text, session_id=session_id)
    if matched:
        return matched[0]
    lower = (user_text or "").lower()
    if "architecture" in lower and "aethos" in lower:
        return architecture_summary_reply()
    if "roadmap" in lower or "mvp" in lower:
        return mvp_roadmap_reply()
    if "reliable" in lower or "fast" in lower:
        return reliability_plan_reply()
    if "mission control" in lower:
        return mission_control_plan_reply()
    if ("different" in lower or "unique" in lower) and "aethos" in lower:
        return differentiation_reply()
    if re.search(r"\bwhy\s+aethos\b", lower) or re.search(r"\w+\s+makes\b.*aethos.*different", lower):
        return differentiation_reply()
    if "checklist" in lower and "test" in lower:
        return test_checklist_reply()
    if "next step" in lower or "do next" in lower:
        from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
            workflow_discovery_preemption_blocks_route,
        )

        if workflow_discovery_preemption_blocks_route(user_text, session_id=session_id):
            return None
        return next_steps_reply()
    return None
