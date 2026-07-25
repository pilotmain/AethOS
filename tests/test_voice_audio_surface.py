# SPDX-License-Identifier: Apache-2.0
"""Voice & audio surface — local-first, flag-gated, governed (never bypasses approval)."""

from fastapi.testclient import TestClient

from aethos_core.api.main import _mount_deferred_routes, app
from aethos_core.config import get_settings
from aethos_core.voice.voice_runtime import (
    get_voice_surface_config,
    prepare_spoken_text,
    synthesize_elevenlabs_speech,
)

_mount_deferred_routes(app)


def test_prepare_spoken_text_drops_code_and_flattens_markdown() -> None:
    """§2 — long code is never read aloud; markdown is flattened for speech."""
    text = (
        "## Plan\n\n"
        "Here is the **plan**:\n"
        "- step one\n"
        "- step two\n"
        "```bash\nrm -rf /\n```\n"
        "See [docs](https://example.com). Inline `value` stays."
    )
    spoken = prepare_spoken_text(text)
    assert "rm -rf" not in spoken
    assert "(code block omitted)" in spoken
    assert "**" not in spoken and "##" not in spoken
    assert "docs" in spoken and "https://example.com" not in spoken
    assert "value" in spoken


def test_prepare_spoken_text_bounds_length() -> None:
    long = "word. " * 600
    spoken = prepare_spoken_text(long)
    assert len(spoken) <= 1300
    assert "reply continues on screen" in spoken


def test_prepare_spoken_text_empty() -> None:
    assert prepare_spoken_text("") == ""
    assert prepare_spoken_text("   \n  ") == ""


def test_voice_surface_config_default_off(monkeypatch) -> None:
    """§4 — every voice capability is honest-off until explicitly enabled."""
    s = get_settings()
    monkeypatch.setattr(s, "voice_surface_enabled", False)
    monkeypatch.setattr(s, "voice_input_enabled", False)
    monkeypatch.setattr(s, "voice_output_enabled", False)
    monkeypatch.setattr(s, "voice_wake_enabled", False)
    cfg = get_voice_surface_config()
    assert cfg["surface_enabled"] is False
    assert cfg["input_enabled"] is False
    assert cfg["output_enabled"] is False
    assert cfg["wake_enabled"] is False
    # The ElevenLabs key is never exposed to the web config.
    assert "elevenlabs_api_key" not in cfg
    assert cfg["elevenlabs_available"] is False


def test_voice_subflags_require_master_switch(monkeypatch) -> None:
    """Sub-capabilities stay off unless the master surface switch is on too."""
    s = get_settings()
    monkeypatch.setattr(s, "voice_surface_enabled", False)
    monkeypatch.setattr(s, "voice_input_enabled", True)
    monkeypatch.setattr(s, "voice_output_enabled", True)
    cfg = get_voice_surface_config()
    assert cfg["input_enabled"] is False
    assert cfg["output_enabled"] is False

    monkeypatch.setattr(s, "voice_surface_enabled", True)
    cfg = get_voice_surface_config()
    assert cfg["input_enabled"] is True
    assert cfg["output_enabled"] is True


def test_elevenlabs_synthesis_requires_provider_and_key(monkeypatch) -> None:
    s = get_settings()
    monkeypatch.setattr(s, "voice_surface_enabled", True)
    monkeypatch.setattr(s, "voice_output_enabled", True)
    monkeypatch.setattr(s, "voice_tts_provider", "system")
    assert synthesize_elevenlabs_speech("hello") is None  # provider is system
    monkeypatch.setattr(s, "voice_tts_provider", "elevenlabs")
    monkeypatch.setattr(s, "elevenlabs_api_key", "")
    assert synthesize_elevenlabs_speech("hello") is None  # no key


def test_voice_config_endpoint_returns_flags(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    get_settings.cache_clear()
    s = get_settings()
    monkeypatch.setattr(s, "voice_surface_enabled", False)
    monkeypatch.setattr(s, "voice_input_enabled", False)
    monkeypatch.setattr(s, "voice_output_enabled", False)
    client = TestClient(app)
    res = client.get("/api/v1/runtime/voice/config")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["surface_enabled"] is False
    assert body["stt_provider"] == "browser"
    assert body["whisper_available"] is False


def test_voice_tts_endpoint_disabled_is_honest(monkeypatch) -> None:
    """§4/§2 — premium TTS endpoint is honestly disabled (503), not silent."""
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    get_settings.cache_clear()
    s = get_settings()
    monkeypatch.setattr(s, "voice_surface_enabled", True)
    monkeypatch.setattr(s, "voice_output_enabled", False)
    monkeypatch.setattr(s, "voice_tts_provider", "elevenlabs")
    monkeypatch.setattr(s, "elevenlabs_api_key", "sk-test")
    client = TestClient(app)
    res = client.post("/api/v1/runtime/voice/tts", json={"text": "hi"})
    assert res.status_code == 503
    assert res.json()["detail"] == "voice_output_disabled"


def test_whisper_transcribe_gated(monkeypatch) -> None:
    from aethos_core.voice.voice_runtime import transcribe_whisper_audio

    s = get_settings()
    monkeypatch.setattr(s, "voice_surface_enabled", False)
    out = transcribe_whisper_audio(b"audio")
    assert out["ok"] is False
    assert out["error"] == "voice_input_disabled"

    monkeypatch.setattr(s, "voice_surface_enabled", True)
    monkeypatch.setattr(s, "voice_input_enabled", True)
    monkeypatch.setattr(s, "voice_stt_provider", "browser")
    out = transcribe_whisper_audio(b"audio")
    assert out["error"] == "whisper_not_configured"


def test_voice_spoken_mutation_stays_governed(monkeypatch) -> None:
    from aethos_core.voice.voice_runtime import process_voice_transcript

    s = get_settings()
    monkeypatch.setattr(s, "voice_surface_enabled", True)
    fake = type(
        "Turn",
        (),
        {"reply": "Preflight required before deploy.", "intent": "mutation", "used_llm": False, "meta": {"preflight_id": "pf-1"}},
    )()
    with __import__("unittest.mock", fromlist=["patch"]).patch(
        "aethos_core.chat.service.resolve_chat_turn",
        return_value=fake,
    ):
        out = process_voice_transcript(transcript="deploy to production", session_id="voice-gov-2")
    assert out["ok"] is True
    assert "Preflight" in str(out.get("reply") or "")
    assert out["meta"]["governance_invariant"] == "voice_never_bypasses_governance"


def test_voice_turn_routes_through_governed_pipeline(monkeypatch) -> None:
    """§4 — a spoken request enters the same governed pipeline (no privileged path)."""
    from aethos_core.voice.voice_runtime import process_voice_transcript

    s = get_settings()
    monkeypatch.setattr(s, "voice_surface_enabled", True)
    out = process_voice_transcript(transcript="show vercel projects", session_id="voice-gov")
    assert out["ok"] is True
    assert out["autonomous_execution_blocked"] is True
    assert out["meta"]["governance_invariant"] == "voice_never_bypasses_governance"
