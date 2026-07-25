# SPDX-License-Identifier: Apache-2.0
"""LLM-backed how-to answers for informational turns — not canned orientation blurbs."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from aethos_core.chat.informational_turn_classifier import (
    is_email_imap_setup_topic,
    is_informational_help_turn,
)
from aethos_core.provider.completion import complete_chat, provider_configured

if TYPE_CHECKING:
    from aethos_core.chat.service import ChatTurnResult

_VAGUE_HELP_RX = re.compile(
    r"^(?:help|help me|i need help|what now|what should i do now)[\s!.?]*$",
    re.I,
)

_LOCAL_WORKSPACE_RX = re.compile(
    r"\b("
    r"local\s+workspace"
    r"|workspace\s+path"
    r"|repo\s+path"
    r"|register\s+(?:a\s+)?(?:repo|path|workspace)"
    r"|add\s+(?:a\s+)?(?:local\s+)?(?:workspace|repo)(?:\s+path)?"
    r"|laptop\s+path"
    r")\b",
    re.I,
)

_PROVIDER_CREDENTIAL_RX = re.compile(
    r"\b("
    r"(?:openai|anthropic|gemini|groq|mistral|railway|vercel|github)\s+(?:api\s+)?(?:key|token)"
    r"|api\s+key"
    r"|provider\s+(?:key|token|credential)"
    r"|add\s+(?:my\s+)?(?:openai|anthropic|api)\s+key"
    r"|where\s+(?:do\s+i|can\s+i|should\s+i)\s+(?:add|put|store)\s+(?:my\s+)?(?:api\s+)?(?:key|token|credential)"
    r")\b",
    re.I,
)

_CANVAS_SETUP_RX = re.compile(
    r"\b("
    r"(?:enable|turn\s+on|activate|use|setup|set\s+up)\b[^.?]{0,40}\bcanvas"
    r"|canvas\b[^.?]{0,40}\b(?:enable|turn\s+on|how\s+do\s+i|how\s+to)"
    r")\b",
    re.I,
)

_CHANNEL_SETUP_RX = re.compile(
    r"\b("
    r"connect\s+(?:a\s+)?channel"
    r"|how\s+(?:do\s+i|to)\s+connect\s+(?:telegram|slack|discord|whatsapp|a\s+channel)"
    r"|where\s+(?:do\s+i|can\s+i)\s+(?:add|connect)\s+(?:telegram|slack|discord|whatsapp|a\s+channel)"
    r"|channel\s+(?:credential|token|bot)"
    r")\b",
    re.I,
)

_CANNED_BLURB_MARKER = "operational intelligence partner"


def is_vague_help_input(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return True
    return bool(_VAGUE_HELP_RX.match(raw))


def is_local_workspace_setup_topic(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    from aethos_core.providers.github.operations.repo_remote_read_api import (
        is_github_remote_repo_analysis_request,
    )

    if is_github_remote_repo_analysis_request(raw):
        return False
    if _LOCAL_WORKSPACE_RX.search(raw):
        return True
    return bool(
        re.search(
            r"\bwhere\s+(?:do\s+i|can\s+i|should\s+i)\b[^.?]{0,80}\b(path|workspace|repo)\b",
            raw,
            re.I,
        )
    )


def is_provider_credential_setup_topic(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _PROVIDER_CREDENTIAL_RX.search(raw))


def is_channel_setup_topic(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _CHANNEL_SETUP_RX.search(raw))


def is_canvas_setup_topic(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    from aethos_core.chat.front_door_intent import is_canvas_render_request

    if is_canvas_render_request(raw):
        return False
    return bool(_CANVAS_SETUP_RX.search(raw))


def compose_canvas_setup_guidance_reply() -> str:
    from aethos_core.config import get_settings
    from aethos_core.mission_control.visible_navigation_registry import capability_truth
    from aethos_core.production.deployment_mode import is_hosted_deployment

    s = get_settings()
    enabled = bool(getattr(s, "canvas_surface_enabled", True))
    canvas_row = capability_truth("canvas")
    surface = (canvas_row or {}).get("surface") or "Canvas tab"

    if enabled:
        return (
            "**Canvas is already enabled** (`CANVAS_SURFACE_ENABLED=true` by default).\n\n"
            "Ask me to **render** something (e.g. \"render a job timeline on the canvas\"). "
            "I'll call `canvas_render` and you view it in the **Canvas** tab — no setup needed."
        )

    if is_hosted_deployment():
        return (
            "Canvas is **disabled** on this deployment.\n\n"
            "Set **`CANVAS_SURFACE_ENABLED=true`** (canonical value — lowercase `true`, not `ON`) "
            "in your **Railway deployment variables**, redeploy, then ask me to render to the Canvas tab.\n\n"
            f"{surface}"
        )
    return (
        "Canvas is **disabled** on this machine.\n\n"
        "Set **`CANVAS_SURFACE_ENABLED=true`** in `.env` and restart the API, then ask me to render "
        "(e.g. \"render a job timeline on the canvas\") and open the **Canvas** tab.\n\n"
        f"{surface}"
    )


def compose_local_workspace_setup_reply() -> str:
    """Deployment-mode-aware repo substrate guidance (hosted §1 spec)."""
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if is_hosted_deployment():
        return (
            "AethOS runs in the cloud, so it **cannot read files on your laptop**.\n\n"
            "To analyze a **GitHub** repository, connect GitHub in **Mission Control → Advanced settings → Credentials** "
            "and ask me to review `owner/repo` or a repo name on GitHub — I read it via the GitHub API "
            "(no local path registration). For laptop-only folders, use a local AethOS install."
        )
    return (
        "Register your repo on this machine under **Mission Control → Code workspaces** "
        "(**Local Workspaces** tab):\n\n"
        "1. Open **Mission Control → Code workspaces**.\n"
        "2. Add the **absolute path** to your repo root (the folder that contains `.git`).\n"
        "3. After it registers, ask me to review or grep the repo — I'll use `repo_*` tools read-only."
    )


def compose_provider_credential_setup_reply() -> str:
    return (
        "Add provider API keys in **Mission Control → Advanced settings → Credentials** — pick the provider card "
        "(OpenAI, Anthropic, Railway, Vercel, GitHub, …) and use **Connect** / save token. "
        "Secrets stay in the **encrypted vault**, scoped to your account.\n\n"
        "For inbox IMAP (not signup email), use **Providers → Email (IMAP/SMTP)** only — "
        "not the Workspace Email triage tab."
    )


def compose_channel_setup_reply() -> str:
    return (
        "Connect messaging channels under **Mission Control → Integrations** (Channels section):\n\n"
        "1. Open **Mission Control → Integrations**.\n"
        "2. Pick the channel (Telegram, Slack, Discord, WhatsApp, …).\n"
        "3. Paste the bot token / credentials in the vault-backed form, then **Test**.\n"
        "4. For Telegram pairing, approve pending chats under **Channels → Pending pairings**."
    )


def _config_surface_hint() -> str:
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if is_hosted_deployment():
        return (
            "On hosted (DEPLOYMENT_MODE=hosted), feature flags are set in the **deployment "
            "provider variables** (e.g. Railway), not a local `.env` file. Use canonical "
            "boolean values: `true` or `false` (never `ON`/`OFF`)."
        )
    return (
        "On local/self-hosted deploys, feature flags are read from `.env` and require a restart. "
        "Use canonical boolean values: `true` or `false` (never `ON`/`OFF`)."
    )


def _informational_context_block() -> str:
    from aethos_core.config import get_settings
    from aethos_core.mission_control.visible_navigation_registry import render_capability_truth_lines
    from aethos_core.production.deployment_mode import deployment_mode

    s = get_settings()
    lines = [
        f"DEPLOYMENT_MODE={deployment_mode()}",
        _config_surface_hint(),
        f"CANVAS_SURFACE_ENABLED={bool(getattr(s, 'canvas_surface_enabled', True))} (default true)",
        "",
        "Allowed operator surfaces (cite ONLY these — never invent settings pages):",
        "- Mission Control → Advanced settings → Credentials (API keys / service credentials)",
        "- Mission Control → Integrations (channel bots)",
        "- Mission Control → Code workspaces (Local Workspaces or Repositories)",
        "- Mission Control → Workspaces → Email (inbox triage — credentials live in Providers)",
        "- Mission Control → Approvals (governed mutations after preflight)",
        "",
    ]
    try:
        lines.extend(render_capability_truth_lines())
    except Exception:  # noqa: BLE001
        pass
    s = get_settings()
    lines.append(
        f"WORKSPACE_SUITE_ENABLED={bool(s.workspace_suite_enabled)} "
        f"MULTI_TENANT_ENABLED={bool(s.multi_tenant_enabled)}"
    )
    return "\n".join(lines)


def _llm_informational_help(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> "ChatTurnResult":
    from aethos_core.chat.service import ChatTurnResult

    raw = (text or "").strip()
    context = _informational_context_block()
    prompt = "\n".join(
        [
            "Answer this specific how-to / where-is question for an AethOS operator.",
            "Be concrete: numbered steps, real UI paths from the context, no generic product pitch.",
            "Do NOT tell them to run mutations or create preflights for informational setup questions.",
            "If a capability flag in the context is already true, say it is enabled — do NOT give setup steps.",
            _config_surface_hint(),
            "",
            context,
            "",
            f"User question (answer exactly this): {raw}",
        ]
    )
    prov = complete_chat(
        prompt,
        session_id=session_id,
        channel=channel,
        include_identity=True,
        system_overlay=(
            "Informational help mode: answer the user's exact question in 3–8 sentences or short bullets. "
            "Never reply with a generic 'ask me to investigate' orientation unless the question is empty."
        ),
    )
    meta = {
        "lane": "informational_help",
        "route_id": "informational_help",
        "suppress_governance_footer": "true",
        "provider": prov.provider,
        "model": prov.model,
    }
    return ChatTurnResult(
        reply=prov.text,
        intent="informational_help",
        used_llm=prov.used_llm,
        provider=prov.provider,
        model=prov.model,
        meta=meta,
    )


def route_informational_help_turn(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> "ChatTurnResult | None":
    """Route informational how-to turns to real answers — not canned orientation blurbs."""
    from aethos_core.chat.front_door_intent import is_capability_question
    from aethos_core.chat.service import ChatTurnResult

    raw = (text or "").strip()
    if not raw:
        return None

    from aethos_core.chat.provider_read_intent import is_provider_read_inventory_request

    if is_provider_read_inventory_request(raw):
        return None

    from aethos_core.chat.informational_turn_classifier import is_explicit_operational_tool_command

    if is_explicit_operational_tool_command(raw):
        return None

    from aethos_core.chat.provider_read_intent import is_provider_health_operational_turn

    if is_provider_health_operational_turn(raw):
        return None

    meta_base = {
        "lane": "informational_help",
        "route_id": "informational_help",
        "suppress_governance_footer": "true",
    }

    if is_vague_help_input(raw):
        from aethos_core.chat.front_door_intent import compose_general_help_reply

        return ChatTurnResult(
            reply=compose_general_help_reply(),
            intent="general_help",
            used_llm=False,
            meta={**meta_base, "topic": "vague"},
        )

    if not is_informational_help_turn(raw, session_id=session_id):
        return None

    if is_capability_question(raw, session_id=session_id) and not is_email_imap_setup_topic(raw):
        return None

    if is_email_imap_setup_topic(raw):
        from aethos_core.chat.email_imap_setup_guidance import compose_email_imap_setup_reply_if_applicable

        imap = compose_email_imap_setup_reply_if_applicable(raw, session_id=session_id)
        if imap is not None:
            body, intent, imap_meta = imap
            merged = {**meta_base, **{k: str(v) for k, v in imap_meta.items()}}
            return ChatTurnResult(reply=body, intent=intent, used_llm=False, meta=merged)

    if is_local_workspace_setup_topic(raw):
        return ChatTurnResult(
            reply=compose_local_workspace_setup_reply(),
            intent="informational_help_local_workspace",
            used_llm=False,
            meta={**meta_base, "topic": "local_workspace"},
        )

    if is_provider_credential_setup_topic(raw):
        return ChatTurnResult(
            reply=compose_provider_credential_setup_reply(),
            intent="informational_help_provider_credentials",
            used_llm=False,
            meta={**meta_base, "topic": "provider_credentials"},
        )

    if is_channel_setup_topic(raw):
        return ChatTurnResult(
            reply=compose_channel_setup_reply(),
            intent="informational_help_channels",
            used_llm=False,
            meta={**meta_base, "topic": "channels"},
        )

    if is_canvas_setup_topic(raw):
        return ChatTurnResult(
            reply=compose_canvas_setup_guidance_reply(),
            intent="informational_help_canvas",
            used_llm=False,
            meta={**meta_base, "topic": "canvas"},
        )

    if provider_configured():
        return _llm_informational_help(raw, session_id=session_id, channel=channel)

    return ChatTurnResult(
        reply=(
            f"I'd answer your question with more detail once a model provider is configured, "
            f"but here's the honest setup path:\n\n{_informational_context_block()}\n\n"
            f"Your question: _{raw[:240]}_"
        ),
        intent="informational_help_not_configured",
        used_llm=False,
        meta={**meta_base, "configured": "false"},
    )


def is_canned_general_help_blurb(reply: str) -> bool:
    return _CANNED_BLURB_MARKER in (reply or "").lower()
