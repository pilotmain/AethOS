# SPDX-License-Identifier: Apache-2.0
"""Voice runtime — conversational interaction across channels."""

from __future__ import annotations

import re
from time import time
from typing import Any

from aethos_core.voice.voice_governance import validate_voice_action, voice_turn_policy

# Spoken replies skip raw code: it reads terribly aloud and is long. We replace
# fenced/inline code with a short spoken placeholder and bound the total length.
_FENCED_CODE_RX = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RX = re.compile(r"`[^`\n]+`")
_LINK_RX = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)")
_HEADING_MARK_RX = re.compile(r"^#{1,6}\s+", re.M)
_LIST_MARK_RX = re.compile(r"^\s*[-*]\s+", re.M)
_EMPHASIS_RX = re.compile(r"[*_]{1,3}([^*_]+)[*_]{1,3}")
_MULTI_NL_RX = re.compile(r"\n{2,}")
_MAX_SPOKEN_CHARS = 1200


def prepare_spoken_text(text: str, *, max_chars: int = _MAX_SPOKEN_CHARS) -> str:
    """Make assistant text speakable: drop code, flatten markdown, bound length.

    Pure + deterministic so both the server (ElevenLabs) and the browser
    (speechSynthesis) speak the same sanitized content. Long code blocks are
    summarized, not read aloud (handoff §2).
    """
    raw = (text or "").strip()
    if not raw:
        return ""
    spoken = _FENCED_CODE_RX.sub(" (code block omitted) ", raw)
    spoken = _INLINE_CODE_RX.sub(lambda m: m.group(0).strip("`"), spoken)
    spoken = _LINK_RX.sub(r"\1", spoken)
    spoken = _HEADING_MARK_RX.sub("", spoken)
    spoken = _LIST_MARK_RX.sub("", spoken)
    spoken = _EMPHASIS_RX.sub(r"\1", spoken)
    spoken = _MULTI_NL_RX.sub(". ", spoken)
    spoken = spoken.replace("\n", ". ")
    spoken = re.sub(r"\s{2,}", " ", spoken).strip()
    spoken = re.sub(r"(\.\s*){2,}", ". ", spoken)
    if len(spoken) > max_chars:
        clipped = spoken[:max_chars]
        cut = clipped.rfind(". ")
        spoken = (clipped[: cut + 1] if cut > max_chars * 0.6 else clipped).strip()
        spoken = f"{spoken} … (reply continues on screen)"
    return spoken


def get_voice_surface_config() -> dict[str, Any]:
    """Web-facing voice config — flags only, never the ElevenLabs key.

    The browser uses this to decide which controls to show. ElevenLabs synthesis
    happens server-side (POST /runtime/voice/tts) so the key never leaves the host.
    """
    from aethos_core.config import get_settings

    s = get_settings()
    surface = bool(getattr(s, "voice_surface_enabled", False))
    provider = str(getattr(s, "voice_tts_provider", "system") or "system").strip().lower()
    elevenlabs_available = bool(provider == "elevenlabs" and str(getattr(s, "elevenlabs_api_key", "") or "").strip())
    stt_provider = str(getattr(s, "voice_stt_provider", "browser") or "browser").strip().lower()
    openai_key = str(getattr(s, "openai_api_key", "") or "").strip()
    whisper_available = bool(stt_provider == "whisper" and openai_key)

    # Per-user preferences override env defaults for wake phrase / wake mode / send mode.
    try:
        from aethos_core.voice.preferences import get_voice_preferences

        prefs = get_voice_preferences()
    except Exception:
        prefs = {"wake_phrase": None, "wake_enabled": False, "auto_send": True, "suggested_wake_phrases": []}

    env_wake = surface and bool(getattr(s, "voice_wake_enabled", False))
    return {
        "ok": True,
        "surface_enabled": surface,
        # Sub-capabilities are only "on" when the master switch is on too.
        "input_enabled": surface and bool(getattr(s, "voice_input_enabled", False)),
        "output_enabled": surface and bool(getattr(s, "voice_output_enabled", False)),
        # wake_available = surface permits it (env); wake_enabled = the user turned it on.
        "wake_available": env_wake,
        "wake_enabled": bool(env_wake and prefs.get("wake_enabled", False)),
        "stt_provider": stt_provider,
        "whisper_available": whisper_available,
        "tts_provider": provider,
        "elevenlabs_available": elevenlabs_available,
        "wake_phrase": str(
            prefs.get("wake_phrase") or getattr(s, "voice_wake_phrase", "hey aethos") or "hey aethos"
        ).strip().lower(),
        "auto_send": bool(prefs.get("auto_send", True)),
        "suggested_wake_phrases": prefs.get("suggested_wake_phrases", []),
    }


def transcribe_whisper_audio(audio_bytes: bytes, *, filename: str = "audio.webm") -> dict[str, Any]:
    """Server-side Whisper STT (optional). Requires voice input + whisper provider + OpenAI key."""
    from aethos_core.config import get_settings

    s = get_settings()
    if not getattr(s, "voice_surface_enabled", False) or not getattr(s, "voice_input_enabled", False):
        return {"ok": False, "error": "voice_input_disabled"}
    if str(getattr(s, "voice_stt_provider", "browser") or "").strip().lower() != "whisper":
        return {"ok": False, "error": "whisper_not_configured"}
    api_key = str(getattr(s, "openai_api_key", "") or "").strip()
    if not api_key:
        return {"ok": False, "error": "openai_key_missing"}
    if not audio_bytes:
        return {"ok": False, "error": "empty_audio"}
    model = str(getattr(s, "voice_whisper_model", "") or "whisper-1").strip() or "whisper-1"
    try:
        import httpx

        files = {"file": (filename, audio_bytes, "application/octet-stream")}
        data = {"model": model}
        resp = httpx.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files=files,
            data=data,
            timeout=60.0,
        )
        if resp.status_code != 200:
            return {"ok": False, "error": "whisper_request_failed", "status": resp.status_code}
        body = resp.json()
        text = str(body.get("text") or "").strip()
        if not text:
            return {"ok": False, "error": "empty_transcript"}
        return {"ok": True, "transcript": text, "provider": "whisper"}
    except Exception as exc:
        return {"ok": False, "error": "whisper_unavailable", "detail": str(exc)[:200]}


def synthesize_elevenlabs_speech(text: str) -> tuple[bytes, str] | None:
    """Server-side ElevenLabs TTS. Returns (audio_bytes, mime) or None when unavailable.

    Gated: requires voice_surface_enabled + voice_output_enabled +
    voice_tts_provider=elevenlabs + a key. The key is read here and never exposed
    to the client. Network failures degrade to None (caller falls back to system).
    """
    from aethos_core.config import get_settings

    s = get_settings()
    if not (getattr(s, "voice_surface_enabled", False) and getattr(s, "voice_output_enabled", False)):
        return None
    if str(getattr(s, "voice_tts_provider", "system") or "").strip().lower() != "elevenlabs":
        return None
    api_key = str(getattr(s, "elevenlabs_api_key", "") or "").strip()
    if not api_key:
        return None
    spoken = prepare_spoken_text(text)
    if not spoken:
        return None
    voice_id = str(getattr(s, "elevenlabs_voice_id", "") or "21m00Tcm4TlvDq8ikWAM").strip()
    model_id = str(getattr(s, "elevenlabs_model_id", "") or "eleven_turbo_v2_5").strip()
    try:
        import httpx

        resp = httpx.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "accept": "audio/mpeg", "content-type": "application/json"},
            json={"text": spoken, "model_id": model_id},
            timeout=30.0,
        )
        if resp.status_code != 200 or not resp.content:
            return None
        return resp.content, "audio/mpeg"
    except Exception:
        return None


def get_voice_status(*, channel: str = "web_voice") -> dict[str, Any]:
    from aethos_core.config import get_settings

    return {
        "ok": True,
        "voice_surface_enabled": bool(getattr(get_settings(), "voice_surface_enabled", False)),
        "phase": "10.0B",
        "channels": ["telegram_voice", "web_voice", "mobile_voice", "call_mode"],
        "features": {
            "realtime_voice": "enabled",
            "push_to_talk": True,
            "interruption_handling": True,
            "call_mode": "governed",
            "multi_language": ["en", "am"],
            "voice_memory": True,
            "ambient_listening": "opt_in_only",
        },
        "policy": voice_turn_policy(channel=channel),
        "autonomous_execution_blocked": True,
        "checked_at": time(),
    }


def process_voice_transcript(
    *,
    transcript: str,
    session_id: str = "default",
    channel: str = "web_voice",
    action_hint: str | None = None,
) -> dict[str, Any]:
    """Process voice transcript through same orchestration brain as chat."""
    from aethos_core.chat.service import resolve_chat_turn
    from aethos_core.config import get_settings
    from aethos_core.relational.relational_runtime import finalize_relational_reply, prepare_relational_turn

    # Voice surface is gated (handoff §11/§21 step 9); default off. A voice request
    # enters the identical /api/v1/chat pipeline — it is never a privileged path.
    if not getattr(get_settings(), "voice_surface_enabled", False):
        return {"ok": False, "reply": None, "error": "voice_surface_disabled"}

    if action_hint:
        gov = validate_voice_action(action_type=action_hint)
        if not gov.get("ok"):
            return {"ok": False, "reply": gov.get("reason"), "governance": gov}

    ctx = prepare_relational_turn(user_text=transcript, session_id=session_id, channel=channel)
    result = resolve_chat_turn(
        transcript,
        session_id=session_id,
        channel=channel,
        surface="voice",
        apply_relational_layer=False,
    )
    reply, meta = finalize_relational_reply(result.reply, emotional_context=ctx, intent=result.intent)
    meta["voice_channel"] = channel
    meta["governance_invariant"] = "voice_never_bypasses_governance"
    return {
        "ok": True,
        "reply": reply,
        "intent": result.intent,
        "meta": meta,
        "used_llm": result.used_llm,
        "autonomous_execution_blocked": True,
    }
