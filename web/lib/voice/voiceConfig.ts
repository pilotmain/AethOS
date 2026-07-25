import { apiBase } from "@/lib/api";

/**
 * Web-facing voice configuration, mirrored from the backend
 * GET /api/v1/runtime/voice/config. Flags only — the ElevenLabs key never
 * leaves the server (premium synthesis runs server-side via /runtime/voice/tts).
 * Everything defaults off (disabled-surface honesty).
 */
export type VoiceConfig = {
  ok: boolean;
  surfaceEnabled: boolean;
  inputEnabled: boolean;
  outputEnabled: boolean;
  wakeEnabled: boolean;
  sttProvider: "browser" | "whisper" | string;
  whisperAvailable: boolean;
  ttsProvider: "system" | "elevenlabs" | string;
  elevenlabsAvailable: boolean;
  wakePhrase: string;
  /** Signed-in operator's first name, for a personalized spoken greeting. */
  operatorName: string;
  /** Surface permits wake mode (env) — distinct from the user having enabled it. */
  wakeAvailable: boolean;
  /** Send captured speech automatically, or drop it in the box for the user to send. */
  autoSend: boolean;
  suggestedWakePhrases: string[];
};

export const VOICE_CONFIG_DISABLED: VoiceConfig = {
  ok: true,
  surfaceEnabled: false,
  inputEnabled: false,
  outputEnabled: false,
  wakeEnabled: false,
  wakeAvailable: false,
  sttProvider: "browser",
  whisperAvailable: false,
  ttsProvider: "system",
  elevenlabsAvailable: false,
  wakePhrase: "hey aethos",
  operatorName: "",
  autoSend: true,
  suggestedWakePhrases: [],
};

export async function saveVoicePreferences(prefs: {
  wake_phrase?: string;
  wake_enabled?: boolean;
  auto_send?: boolean;
}): Promise<boolean> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/runtime/voice/preferences`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(prefs),
    });
    return res.ok;
  } catch {
    return false;
  }
}

type RawVoiceConfig = {
  ok?: boolean;
  surface_enabled?: boolean;
  input_enabled?: boolean;
  output_enabled?: boolean;
  wake_enabled?: boolean;
  wake_available?: boolean;
  stt_provider?: string;
  whisper_available?: boolean;
  tts_provider?: string;
  elevenlabs_available?: boolean;
  wake_phrase?: string;
  operator_name?: string;
  auto_send?: boolean;
  suggested_wake_phrases?: string[];
};

export async function fetchVoiceConfig(): Promise<VoiceConfig> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/runtime/voice/config`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return VOICE_CONFIG_DISABLED;
    const raw = (await res.json()) as RawVoiceConfig;
    return {
      ok: raw.ok !== false,
      surfaceEnabled: Boolean(raw.surface_enabled),
      inputEnabled: Boolean(raw.input_enabled),
      outputEnabled: Boolean(raw.output_enabled),
      wakeEnabled: Boolean(raw.wake_enabled),
      wakeAvailable: Boolean(raw.wake_available),
      sttProvider: (raw.stt_provider as VoiceConfig["sttProvider"]) || "browser",
      whisperAvailable: Boolean(raw.whisper_available),
      ttsProvider: (raw.tts_provider as VoiceConfig["ttsProvider"]) || "system",
      elevenlabsAvailable: Boolean(raw.elevenlabs_available),
      wakePhrase: (raw.wake_phrase || "hey aethos").toLowerCase().trim(),
      operatorName: (raw.operator_name || "").trim(),
      autoSend: raw.auto_send !== false,
      suggestedWakePhrases: raw.suggested_wake_phrases || [],
    };
  } catch {
    return VOICE_CONFIG_DISABLED;
  }
}
