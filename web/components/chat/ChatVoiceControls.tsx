"use client";

import { useEffect, useState } from "react";

import { mcAlpha, mcColors } from "@/lib/missionControl/layout";
import type { VoiceController } from "@/lib/voice/useVoice";
import { saveVoicePreferences } from "@/lib/voice/voiceConfig";

type Props = {
  voice: VoiceController;
  /** Disable interactive capture while a turn is sending (replies can still be spoken). */
  busy?: boolean;
};

const pillStyle = (active: boolean, tone: string) => ({
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  padding: "5px 10px",
  borderRadius: 999,
  fontSize: 11,
  fontWeight: 600,
  cursor: "pointer",
  border: `1px solid ${active ? tone : mcColors.borderSubtle}`,
  background: active ? mcAlpha(tone, 14) : "transparent",
  color: active ? tone : mcColors.textMuted,
});

/**
 * Voice controls for the composer (handoff §1–§5). Renders only what the
 * server-reported config enables; when the surface is off (or the browser lacks
 * the Web Speech API) it stays honest — the mic still surfaces a clear reason on
 * click rather than silently doing nothing. The live-mic indicator is always
 * visible while listening (privacy).
 */
export function ChatVoiceControls({ voice, busy }: Props) {
  const { config } = voice;
  const [showSettings, setShowSettings] = useState(false);
  const [phrase, setPhrase] = useState("");
  const [wantWake, setWantWake] = useState(false);
  const [autoSend, setAutoSend] = useState(true);
  const [saving, setSaving] = useState(false);

  // Seed the settings form from the loaded config.
  useEffect(() => {
    if (config) {
      setPhrase(config.wakePhrase);
      setWantWake(config.wakeEnabled);
      setAutoSend(config.autoSend);
    }
  }, [config]);

  async function saveSettings() {
    setSaving(true);
    try {
      await saveVoicePreferences({
        wake_phrase: phrase.trim() || "hey aethos",
        wake_enabled: wantWake,
        auto_send: autoSend,
      });
      voice.reloadConfig();
      setShowSettings(false);
    } finally {
      setSaving(false);
    }
  }

  // Config still loading — render nothing rather than flicker controls.
  if (!config) return null;

  const surfaceOff = !config.surfaceEnabled;
  const micReady = config.surfaceEnabled && config.inputEnabled && (voice.sttSupported || config.whisperAvailable);

  // §5 — surface enabled but the browser can't capture: an honest note, no mic.
  if (config.surfaceEnabled && config.inputEnabled && !voice.sttSupported && !config.whisperAvailable) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 4, width: "100%", margin: "0 0 6px" }}>
        <span style={{ fontSize: 11, color: mcColors.textDim }}>
          Your browser doesn&apos;t support voice input. Voice replies may still work.
        </span>
      </div>
    );
  }

  const live = voice.listening || voice.talkMode;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        width: "100%",
        margin: "0 0 6px",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        {surfaceOff ? (
          <span
            role="status"
            style={{ fontSize: 11, fontWeight: 600, color: mcColors.textDim, paddingRight: 4 }}
          >
            Voice off
          </span>
        ) : micReady && !live ? (
          <span role="status" style={{ fontSize: 11, color: mcColors.textMuted, paddingRight: 4 }}>
            Mic ready
          </span>
        ) : null}
        <button
          type="button"
          onClick={voice.toggleListening}
          disabled={busy && !voice.listening}
          aria-pressed={voice.listening}
          aria-label={voice.listening ? "Stop voice input" : "Start voice input"}
          title={surfaceOff ? "Voice is turned off for this deployment — ask AethOS in chat how to enable it" : "Hold a thought — speak to AethOS"}
          style={{
            ...pillStyle(voice.listening, mcColors.red),
            opacity: surfaceOff ? 0.7 : 1,
          }}
        >
          <span aria-hidden="true">{voice.listening ? "●" : "🎙"}</span>
          {voice.listening ? "Recording…" : "Mic"}
        </button>

        {config.wakeEnabled ? (
          <button
            type="button"
            onClick={voice.toggleTalkMode}
            aria-pressed={voice.talkMode}
            aria-label={voice.talkMode ? "Stop hands-free listening" : "Start hands-free listening"}
            title={`Hands-free — say "${config.wakePhrase}" to AethOS`}
            style={pillStyle(voice.talkMode, mcColors.cyan)}
          >
            <span aria-hidden="true">{voice.talkMode ? "📡" : "🛰"}</span>
            {voice.talkMode ? `Listening for "${config.wakePhrase}"` : "Hands-free"}
          </button>
        ) : null}

        {config.outputEnabled ? (
          <button
            type="button"
            onClick={voice.toggleSpeakReplies}
            aria-pressed={voice.speakReplies}
            aria-label={voice.speakReplies ? "Mute spoken replies" : "Speak replies aloud"}
            title="Read AethOS replies aloud"
            style={pillStyle(voice.speakReplies, mcColors.green)}
          >
            <span aria-hidden="true">{voice.speakReplies ? "🔊" : "🔈"}</span>
            {voice.speakReplies ? "Speaking on" : "Speak replies"}
          </button>
        ) : null}

        {voice.speaking ? (
          <button
            type="button"
            onClick={voice.stopSpeaking}
            aria-label="Stop speaking"
            style={pillStyle(true, mcColors.amber)}
          >
            <span aria-hidden="true">■</span> Stop voice
          </button>
        ) : null}

        {config.surfaceEnabled && config.inputEnabled ? (
          <button
            type="button"
            onClick={() => setShowSettings((v) => !v)}
            aria-label="Voice settings"
            aria-expanded={showSettings}
            title="Voice settings — wake word & send mode"
            style={pillStyle(showSettings, mcColors.textMuted)}
          >
            <span aria-hidden="true">⚙</span> Voice settings
          </button>
        ) : null}

        {live ? (
          <span
            role="status"
            aria-live="polite"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              fontSize: 11,
              fontWeight: 600,
              color: mcColors.red,
            }}
          >
            <span
              aria-hidden="true"
              style={{
                width: 8,
                height: 8,
                borderRadius: 999,
                background: mcColors.red,
                boxShadow: `0 0 0 0 ${mcAlpha(mcColors.red, 60)}`,
                animation: "aethosMicPulse 1.4s ease-out infinite",
              }}
            />
            Mic is live
          </span>
        ) : null}
      </div>

      {showSettings ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            padding: "12px 14px",
            borderRadius: 10,
            border: `1px solid ${mcColors.borderSubtle}`,
            background: mcAlpha(mcColors.cyan, 6),
          }}
        >
          <label style={{ fontSize: 11, color: mcColors.textMuted, display: "flex", flexDirection: "column", gap: 4 }}>
            Wake word (say this to start hands-free)
            <input
              value={phrase}
              onChange={(e) => setPhrase(e.target.value)}
              placeholder="hey aethos"
              maxLength={40}
              style={{
                padding: "6px 8px",
                borderRadius: 6,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(0,0,0,0.35)",
                color: mcColors.text,
                fontSize: 12,
                maxWidth: 320,
              }}
            />
          </label>
          {config.suggestedWakePhrases.length > 0 ? (
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {config.suggestedWakePhrases.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setPhrase(s)}
                  style={{ ...pillStyle(phrase === s, mcColors.cyan), padding: "3px 8px" }}
                >
                  {s}
                </button>
              ))}
            </div>
          ) : null}
          <label style={{ fontSize: 12, color: mcColors.text, display: "flex", alignItems: "center", gap: 8 }}>
            <input type="checkbox" checked={wantWake} onChange={(e) => setWantWake(e.target.checked)} />
            Enable hands-free wake word
            {!config.wakeAvailable ? (
              <span style={{ fontSize: 10, color: mcColors.textDim }}>(needs VOICE_WAKE_ENABLED on the server)</span>
            ) : null}
          </label>
          <label style={{ fontSize: 12, color: mcColors.text, display: "flex", alignItems: "center", gap: 8 }}>
            <input type="checkbox" checked={autoSend} onChange={(e) => setAutoSend(e.target.checked)} />
            Send automatically after I finish speaking (off = review, then click send)
          </label>
          {config.outputEnabled && voice.voices.length > 0 ? (
            <label style={{ fontSize: 11, color: mcColors.textMuted, display: "flex", flexDirection: "column", gap: 4 }}>
              Reply voice (male / female / accent)
              <select
                value={voice.voiceURI}
                onChange={(e) => voice.setVoiceURI(e.target.value)}
                style={{
                  padding: "6px 8px",
                  borderRadius: 6,
                  border: `1px solid ${mcColors.borderSubtle}`,
                  background: "rgba(0,0,0,0.35)",
                  color: mcColors.text,
                  fontSize: 12,
                  maxWidth: 340,
                }}
              >
                <option value="">Browser default</option>
                {voice.voices.map((v) => (
                  <option key={v.voiceURI} value={v.voiceURI}>
                    {v.name} · {v.lang}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              onClick={saveSettings}
              disabled={saving}
              style={pillStyle(true, mcColors.green)}
            >
              {saving ? "Saving…" : "Save"}
            </button>
            <button type="button" onClick={() => setShowSettings(false)} style={pillStyle(false, mcColors.textMuted)}>
              Cancel
            </button>
          </div>
        </div>
      ) : null}

      {voice.interim ? (
        <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted, fontStyle: "italic" }}>
          “{voice.interim}”
        </p>
      ) : null}

      {voice.error ? (
        <p style={{ margin: 0, fontSize: 11, color: mcColors.amber }}>
          {voice.error}{" "}
          <button
            type="button"
            onClick={voice.clearError}
            style={{ background: "none", border: "none", color: mcColors.textDim, cursor: "pointer", fontSize: 11 }}
          >
            dismiss
          </button>
        </p>
      ) : null}

      <style>{`@keyframes aethosMicPulse {
        0% { box-shadow: 0 0 0 0 ${mcAlpha(mcColors.red, 55)}; }
        70% { box-shadow: 0 0 0 7px ${mcAlpha(mcColors.red, 0)}; }
        100% { box-shadow: 0 0 0 0 ${mcAlpha(mcColors.red, 0)}; }
      }`}</style>
    </div>
  );
}
