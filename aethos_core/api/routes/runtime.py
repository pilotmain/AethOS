# SPDX-License-Identifier: Apache-2.0

from fastapi import APIRouter, File, Request, UploadFile
from pydantic import BaseModel, Field

from aethos_core.config import get_settings
from aethos_core.provider.completion import provider_configured
from aethos_core.runtime.authority import TransportState, authority

router = APIRouter(tags=["runtime"])


class McpInvokeIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    arguments: dict[str, object] | None = None


class VectorRememberIn(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    tags: list[str] = Field(default_factory=list)


class VectorRecallIn(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class SessionLinkIn(BaseModel):
    session_ids: list[str] = Field(min_length=1, max_length=8)
    canonical_session_id: str | None = Field(default=None, max_length=64)


@router.get("/runtime/status")
def get_runtime_status() -> dict[str, object]:
    """Observational runtime snapshot — does not affect chat."""
    s = get_settings()
    snap = authority.snapshot()
    caps = authority.capabilities
    configured = provider_configured()
    status = "ok" if snap.transport == TransportState.REACHABLE else "degraded"
    from aethos_core.runtime.tunnel.tunnel_manager import tunnel_status

    tunnel = tunnel_status()
    from aethos_core.runtime.operational_environment import resolve_operational_environment

    environment = resolve_operational_environment()
    from aethos_core.governance.approval_privacy_governance import governance_diagnostics_snapshot

    governance = governance_diagnostics_snapshot()
    return {
        "status": status,
        "chat_ready": snap.chat_ready,
        "api_port": s.api_port,
        "operational_environment": environment.to_dict(),
        "environment_banner": environment.banner,
        "governance_diagnostics": governance,
        "tunnel": tunnel.get("tunnel"),
        "provider": {
            "real_llm": s.use_real_llm,
            "active_provider": s.active_provider,
            "model": s.anthropic_model,
            "ready": configured,
        },
        "capabilities": {
            "browser_automation": caps["browser_automation_enabled"],
            "host_executor": caps["host_executor_enabled"],
            "vercel_cli_on_path": caps["vercel_cli_on_path"],
        },
    }


@router.get("/runtime/tunnel/status")
def get_tunnel_status_api() -> dict[str, object]:
    from aethos_core.runtime.tunnel.tunnel_manager import tunnel_status

    return tunnel_status()


@router.post("/runtime/tunnel/start")
def start_tunnel_api() -> dict[str, object]:
    from aethos_core.runtime.tunnel.tunnel_manager import start_tunnel

    return start_tunnel()


@router.post("/runtime/tunnel/stop")
def stop_tunnel_api() -> dict[str, object]:
    from aethos_core.runtime.tunnel.tunnel_manager import stop_tunnel

    return stop_tunnel()


@router.post("/runtime/tunnel/restart")
def restart_tunnel_api() -> dict[str, object]:
    from aethos_core.runtime.tunnel.tunnel_manager import restart_tunnel

    return restart_tunnel()


@router.get("/runtime/mcp/tools")
def get_mcp_tools() -> dict[str, object]:
    from aethos_core.operational_skill_runtime.skill_loader import mcp_tool_catalog

    return mcp_tool_catalog()


@router.post("/runtime/mcp/invoke")
def post_mcp_invoke(body: McpInvokeIn) -> dict[str, object]:
    from aethos_core.operational_skill_runtime.skill_loader import invoke_mcp_tool

    return invoke_mcp_tool(body.name, arguments=body.arguments)


@router.get("/runtime/skills/local")
def get_local_operator_skills() -> dict[str, object]:
    from aethos_core.operational_skill_runtime.skill_loader import local_operator_skills_snapshot

    return local_operator_skills_snapshot()


@router.get("/runtime/skills/catalog")
def get_governed_skill_catalog() -> dict[str, object]:
    """Governed skill marketplace (phase 1): each skill with its parsed manifest +
    risk classification (read-only vs governed-mutation) so it can be reviewed
    before it's trusted."""
    from aethos_core.skills.manifest import governed_skill_catalog

    return governed_skill_catalog()


@router.get("/runtime/skills/local/{skill_id:path}")
def get_local_operator_skill_route(skill_id: str) -> dict[str, object]:
    from aethos_core.operational_skill_runtime.skill_loader import get_local_operator_skill

    row = get_local_operator_skill(skill_id)
    if row is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="skill_not_found")
    return {"ok": True, "skill": row}


@router.get("/runtime/models")
def get_runtime_models(session_id: str = "default") -> dict[str, object]:
    from aethos_core.llm.model_catalog import model_catalog_snapshot

    return model_catalog_snapshot(session_id=session_id.strip()[:64] or "default")


class SessionModelOverrideBody(BaseModel):
    catalog_id: str | None = Field(default=None, max_length=120)


@router.put("/runtime/sessions/{session_id}/model-override")
def put_session_model_override(session_id: str, body: SessionModelOverrideBody) -> dict[str, object]:
    from aethos_core.llm.session_model_override import set_session_model_override

    return set_session_model_override(session_id, body.catalog_id)


@router.delete("/runtime/sessions/{session_id}/model-override")
def delete_session_model_override(session_id: str) -> dict[str, object]:
    from aethos_core.llm.session_model_override import clear_session_model_override

    return clear_session_model_override(session_id)


@router.get("/runtime/llm/providers")
def get_llm_providers() -> dict[str, object]:
    from aethos_core.llm.provider_router import list_available_llm_providers

    return {"ok": True, "providers": list_available_llm_providers()}


@router.get("/runtime/memory/snapshot")
def get_vector_memory_snapshot(limit: int = 5) -> dict[str, object]:
    from aethos_core.memory.vector_store import memory_snapshot

    return memory_snapshot(limit=min(max(limit, 1), 20))


@router.post("/runtime/memory/remember")
def post_vector_remember(body: VectorRememberIn) -> dict[str, object]:
    from aethos_core.memory.vector_store import remember

    return remember(text=body.text, tags=body.tags)


@router.post("/runtime/memory/recall")
def post_vector_recall(body: VectorRecallIn) -> dict[str, object]:
    from aethos_core.memory.vector_store import recall

    return recall(query=body.query, limit=body.limit)


@router.post("/runtime/sessions/link")
def post_session_link(body: SessionLinkIn) -> dict[str, object]:
    from aethos_core.channels.session_alias import link_session_ids

    return link_session_ids(session_ids=body.session_ids, canonical_session_id=body.canonical_session_id)


@router.get("/runtime/sessions/{session_id}/group")
def get_session_group_route(session_id: str) -> dict[str, object]:
    from aethos_core.channels.session_alias import get_session_group

    return get_session_group(session_id.strip()[:64] or "default")


@router.get("/runtime/agent-tool-policy")
def get_agent_tool_policy(channel: str = "chat") -> dict[str, object]:
    from aethos_core.execution_brain.agent_tool_policy import policy_snapshot

    return policy_snapshot(channel=channel)


@router.get("/runtime/agent-tool-policy/matrix")
def get_agent_tool_policy_matrix() -> dict[str, object]:
    from aethos_core.execution_brain.agent_tool_policy import list_channel_policy_matrix

    return list_channel_policy_matrix()


@router.get("/runtime/cron/status")
def get_cron_governed_status() -> dict[str, object]:
    from aethos_core.jobs.cron_bridge import cron_governed_status

    return cron_governed_status()


@router.get("/runtime/sandbox/status")
def get_sandbox_status() -> dict[str, object]:
    from aethos_core.runtime.governed_sandbox import sandbox_runtime_status

    return sandbox_runtime_status()


class SandboxProbeIn(BaseModel):
    command: str = Field(min_length=1, max_length=500)
    session_id: str = Field(default="operator", max_length=64)


@router.post("/runtime/sandbox/probe")
def post_sandbox_probe(body: SandboxProbeIn) -> dict[str, object]:
    from aethos_core.runtime.governed_sandbox import propose_sandbox_probe

    return propose_sandbox_probe(command=body.command, session_id=body.session_id)


@router.get("/runtime/sessions/{session_id}/meta")
def get_operational_session_meta(session_id: str) -> dict[str, object]:
    from aethos_core.operational_session.operational_session import operational_session_meta

    return {"ok": True, **operational_session_meta(session_id=session_id)}


@router.get("/runtime/sessions/registry")
def get_operator_session_registry() -> dict[str, object]:
    from aethos_core.autonomous_execution.runtime_state import operator_session_registry

    return operator_session_registry()


@router.get("/runtime/cloud/inventory")
def get_cloud_readonly_inventory(session_id: str = "default") -> dict[str, object]:
    from aethos_core.providers.cloud.readonly_inventory import list_cloud_readonly_inventory

    return list_cloud_readonly_inventory(session_id=session_id)


@router.get("/runtime/cloud/inventory/{provider}")
def get_cloud_readonly_inventory_provider(provider: str, session_id: str = "default") -> dict[str, object]:
    from aethos_core.providers.cloud.readonly_inventory import fetch_cloud_readonly_inventory

    return fetch_cloud_readonly_inventory(provider=provider, session_id=session_id)


@router.get("/runtime/onboarding/companion")
def get_companion_onboarding_state() -> dict[str, object]:
    from aethos_core.onboarding.companion_onboarding import build_companion_onboarding_state

    return build_companion_onboarding_state().to_dict()


class SocialDraftIn(BaseModel):
    platform: str = Field(default="linkedin", max_length=32)
    topic: str = Field(min_length=1, max_length=500)


@router.post("/runtime/social/drafts")
def schedule_social_draft_api(body: SocialDraftIn) -> dict[str, object]:
    from aethos_core.social.orchestration import schedule_social_draft

    return schedule_social_draft(platform=body.platform, topic=body.topic).to_dict()


@router.get("/runtime/social/drafts")
def list_social_drafts_api(limit: int = 20) -> dict[str, object]:
    from aethos_core.social.orchestration import list_social_drafts

    drafts = list_social_drafts(limit=limit)
    return {"ok": True, "drafts": drafts, "count": len(drafts), "published": False}


@router.get("/runtime/self-improvement/plan")
def get_self_improvement_plan(repository: str, issue_number: int | None = None) -> dict[str, object]:
    from aethos_core.self_improvement.service import build_self_improvement_plan

    return build_self_improvement_plan(repository=repository, issue_number=issue_number).to_dict()


class OperatorPersonaIn(BaseModel):
    name: str | None = Field(default=None, max_length=80)
    timezone: str | None = Field(default=None, max_length=64)
    work_start_hour: int | None = Field(default=None, ge=0, le=23)
    work_end_hour: int | None = Field(default=None, ge=0, le=23)
    tone: str | None = Field(default=None, max_length=24)
    goals: list[str] | None = Field(default=None)
    first_run_complete: bool | None = None


class OperatorLoginIn(BaseModel):
    passphrase: str = Field(default="", max_length=256)


@router.get("/runtime/onboarding/persona-state")
def onboarding_persona_state_api() -> dict[str, object]:
    """First-run / login state for the AethOS gate (Stage 3)."""
    s = get_settings()
    from aethos_core.onboarding.operator_persona import get_persona

    persona = get_persona()
    return {
        "ok": True,
        "login_enabled": bool(s.aethos_login_enabled),
        "login_required": bool(s.aethos_login_enabled and s.aethos_login_passphrase.strip()),
        "onboarding_enabled": bool(s.aethos_onboarding_enabled),
        "first_run": not bool(persona.get("first_run_complete")),
        "persona": persona,
    }


@router.post("/runtime/onboarding/login")
def onboarding_login_api(body: OperatorLoginIn) -> dict[str, object]:
    """Verify the operator passphrase when the login gate is enabled."""
    import hashlib
    import hmac

    s = get_settings()
    if not s.aethos_login_enabled:
        return {"ok": True, "token": "open", "login_enabled": False}
    expected = s.aethos_login_passphrase.strip()
    if not expected:
        return {"ok": True, "token": "open", "login_enabled": True, "note": "no passphrase configured"}
    if hmac.compare_digest(body.passphrase.strip(), expected):
        token = hashlib.sha256(f"aethos-operator:{expected}".encode()).hexdigest()[:32]
        return {"ok": True, "token": token}
    return {"ok": False, "error": "invalid_passphrase"}


@router.put("/runtime/onboarding/persona")
def onboarding_persona_save_api(body: OperatorPersonaIn) -> dict[str, object]:
    """Persist the first-run rapport persona (local-only personalization)."""
    from aethos_core.onboarding.operator_persona import save_persona

    persona = save_persona(
        name=body.name,
        timezone=body.timezone,
        work_start_hour=body.work_start_hour,
        work_end_hour=body.work_end_hour,
        tone=body.tone,
        goals=body.goals,
        first_run_complete=body.first_run_complete,
    )
    return {"ok": True, "persona": persona}


class VoiceTtsIn(BaseModel):
    text: str = Field(min_length=1, max_length=12_000)


class VoicePreferencesIn(BaseModel):
    wake_phrase: str | None = None
    wake_enabled: bool | None = None
    auto_send: bool | None = None


@router.get("/runtime/voice/config")
def voice_config_api(request: Request) -> dict[str, object]:
    """Web-facing voice config (flags only). Drives which voice controls render.

    Never returns the ElevenLabs key — premium synthesis runs server-side via
    POST /runtime/voice/tts. All flags default off (disabled-surface honesty).
    """
    from aethos_core.voice.voice_runtime import get_voice_surface_config

    config = get_voice_surface_config()
    # Operator first name for a personalized spoken greeting (from the signed-in user).
    try:
        from aethos_core.api.routes.aethos_identity import current_user

        user = current_user(request) or {}
        name = str(user.get("name") or "").strip()
        if not name:
            email = str(user.get("email") or "")
            name = email.split("@")[0] if email else ""
        config["operator_name"] = name.split()[0] if name else ""
    except Exception:
        config["operator_name"] = ""
    return config


@router.get("/runtime/voice/preferences")
def voice_preferences_get_api() -> dict[str, object]:
    """Per-user voice preferences (wake phrase, wake mode on/off, auto-send)."""
    from aethos_core.voice.preferences import get_voice_preferences

    return {"ok": True, "preferences": get_voice_preferences()}


@router.put("/runtime/voice/preferences")
def voice_preferences_put_api(body: VoicePreferencesIn) -> dict[str, object]:
    """Update this user's voice preferences. The wake phrase is theirs to choose."""
    from aethos_core.voice.preferences import set_voice_preferences

    prefs = set_voice_preferences(
        wake_phrase=body.wake_phrase, wake_enabled=body.wake_enabled, auto_send=body.auto_send
    )
    return {"ok": True, "preferences": prefs}


@router.post("/runtime/voice/tts")
def voice_tts_api(body: VoiceTtsIn):
    """Premium (ElevenLabs) text-to-speech. Returns audio/mpeg, or an honest 503.

    System-voice TTS is browser-side; this endpoint only serves the optional
    ElevenLabs upgrade so the key stays server-side. Disabled / unconfigured
    states return a clear error instead of silently doing nothing.
    """
    from fastapi import HTTPException
    from fastapi.responses import Response

    from aethos_core.voice.voice_runtime import get_voice_surface_config, synthesize_elevenlabs_speech

    config = get_voice_surface_config()
    if not config.get("output_enabled"):
        raise HTTPException(status_code=503, detail="voice_output_disabled")
    if not config.get("elevenlabs_available"):
        raise HTTPException(status_code=503, detail="elevenlabs_unavailable")
    audio = synthesize_elevenlabs_speech(body.text)
    if audio is None:
        raise HTTPException(status_code=502, detail="tts_synthesis_failed")
    content, mime = audio
    return Response(content=content, media_type=mime, headers={"Cache-Control": "no-store"})


@router.post("/runtime/voice/transcribe")
async def voice_transcribe_api(audio: UploadFile = File(...)) -> dict[str, object]:
    """Optional Whisper speech-to-text. Audio stays server-side; returns transcript text."""
    from fastapi import HTTPException

    from aethos_core.voice.voice_runtime import transcribe_whisper_audio

    raw = await audio.read()
    result = transcribe_whisper_audio(raw, filename=audio.filename or "audio.webm")
    if not result.get("ok"):
        error = str(result.get("error") or "transcription_failed")
        status = 503 if error.endswith("_disabled") or "not_configured" in error or "missing" in error else 502
        raise HTTPException(status_code=status, detail=error)
    return result
