import { apiBase } from "@/lib/api";

/**
 * Spoken replies. Default path is the browser's free system voices
 * (speechSynthesis); when the server reports an ElevenLabs upgrade is available
 * we fetch synthesized audio from /runtime/voice/tts (the key stays server-side)
 * and play it. Long code blocks are never read aloud (see prepareSpokenText).
 */

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

export type SpeechVoice = { voiceURI: string; name: string; lang: string };

/** Available system voices (name/lang/accent). Browsers load these lazily, so callers may
 * need to re-read after the 'voiceschanged' event. */
export function listSpeechVoices(): SpeechVoice[] {
  if (!isSpeechSynthesisSupported()) return [];
  try {
    return window.speechSynthesis
      .getVoices()
      .map((v) => ({ voiceURI: v.voiceURI, name: v.name, lang: v.lang }))
      .sort((a, b) => a.lang.localeCompare(b.lang) || a.name.localeCompare(b.name));
  } catch {
    return [];
  }
}

/** Subscribe to the voice list becoming available/changing. Returns an unsubscribe fn. */
export function onVoicesChanged(cb: () => void): () => void {
  if (!isSpeechSynthesisSupported()) return () => {};
  window.speechSynthesis.addEventListener("voiceschanged", cb);
  return () => window.speechSynthesis.removeEventListener("voiceschanged", cb);
}

/** Pick a good-sounding default voice when the user hasn't chosen one. Prefers Google /
 * natural English voices (fast + clear) over the OS default, which is often slow/robotic. */
export function pickDefaultVoiceURI(voices: SpeechVoice[]): string {
  if (!voices.length) return "";
  const score = (v: SpeechVoice): number => {
    const n = v.name.toLowerCase();
    const l = v.lang.toLowerCase();
    let s = 0;
    if (n.includes("google")) s += 5;
    if (n.includes("natural") || n.includes("premium") || n.includes("neural")) s += 3;
    if (l.startsWith("en")) s += 2;
    if (l === "en-gb" || l === "en-us") s += 1;
    return s;
  };
  return [...voices].sort((a, b) => score(b) - score(a))[0].voiceURI;
}

const FENCED_CODE = /```[\s\S]*?```/g;
const INLINE_CODE = /`[^`\n]+`/g;
const LINK = /\[([^\]]+)\]\((?:[^)]+)\)/g;
const HEADING = /^#{1,6}\s+/gm;
const LIST = /^\s*[-*]\s+/gm;
const EMPHASIS = /[*_]{1,3}([^*_]+)[*_]{1,3}/g;
// Lines that are only separator characters: --- , *** , ___ , or a table rule | --- | --- |
const SEPARATOR_LINE = /^[ \t]*[|:*_-][ \t|:*_-]{2,}$/gm;
const TABLE_PIPE = /[ \t]*\|[ \t]*/g; // remaining table column dividers → pause
const EMOJI = /[\p{Extended_Pictographic}\u{FE0F}\u{20E3}]/gu;
const MULTI_NL = /\n{2,}/g;
const MAX_SPOKEN = 1200;

/** Mirror of the server prepare_spoken_text so both paths speak the same text. */
export function prepareSpokenText(text: string): string {
  const raw = (text || "").trim();
  if (!raw) return "";
  let spoken = raw.replace(FENCED_CODE, " (code block omitted) ");
  spoken = spoken.replace(INLINE_CODE, (m) => m.replace(/`/g, ""));
  spoken = spoken.replace(LINK, "$1");
  spoken = spoken.replace(HEADING, "");
  spoken = spoken.replace(LIST, "");
  spoken = spoken.replace(EMPHASIS, "$1");
  // Drop horizontal rules / table separator rows, soften remaining table pipes, remove emojis —
  // so it reads like a person, not "dash dash dash, pipe, card index dividers".
  spoken = spoken.replace(SEPARATOR_LINE, "");
  spoken = spoken.replace(TABLE_PIPE, ", ");
  spoken = spoken.replace(EMOJI, "");
  spoken = spoken.replace(MULTI_NL, ". ").replace(/\n/g, ". ");
  spoken = spoken.replace(/\s{2,}/g, " ").trim();
  spoken = spoken.replace(/(\.\s*){2,}/g, ". ");
  if (spoken.length > MAX_SPOKEN) {
    const clipped = spoken.slice(0, MAX_SPOKEN);
    const cut = clipped.lastIndexOf(". ");
    spoken = `${(cut > MAX_SPOKEN * 0.6 ? clipped.slice(0, cut + 1) : clipped).trim()} … (reply continues on screen)`;
  }
  return spoken;
}

export type SpeakOptions = {
  provider?: "system" | "elevenlabs" | string;
  elevenlabsAvailable?: boolean;
  /** Preferred system voice (voiceURI). Picks male/female/accent per the user's choice. */
  voiceURI?: string;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
};

let currentAudio: HTMLAudioElement | null = null;

export function stopSpeaking(): void {
  if (typeof window === "undefined") return;
  if (isSpeechSynthesisSupported()) {
    try {
      window.speechSynthesis.cancel();
    } catch {
      /* noop */
    }
  }
  if (currentAudio) {
    try {
      currentAudio.pause();
      currentAudio.src = "";
    } catch {
      /* noop */
    }
    currentAudio = null;
  }
}

function speakSystem(text: string, opts: SpeakOptions): void {
  if (!isSpeechSynthesisSupported()) {
    opts.onError?.("speech_synthesis_unsupported");
    opts.onEnd?.();
    return;
  }
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.02;
  utterance.pitch = 1.0;
  if (opts.voiceURI) {
    try {
      const match = window.speechSynthesis.getVoices().find((v) => v.voiceURI === opts.voiceURI);
      if (match) {
        utterance.voice = match;
        utterance.lang = match.lang;
      }
    } catch {
      /* fall back to default voice */
    }
  }
  utterance.onstart = () => opts.onStart?.();
  utterance.onend = () => opts.onEnd?.();
  utterance.onerror = () => {
    opts.onError?.("speech_synthesis_error");
    opts.onEnd?.();
  };
  try {
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  } catch {
    opts.onError?.("speech_synthesis_error");
    opts.onEnd?.();
  }
}

async function speakElevenLabs(rawText: string, spoken: string, opts: SpeakOptions): Promise<void> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/runtime/voice/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "audio/mpeg" },
      body: JSON.stringify({ text: rawText }),
    });
    if (!res.ok) {
      // Honest fallback to free system voices when premium synthesis is down.
      speakSystem(spoken, opts);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    currentAudio = audio;
    audio.onplay = () => opts.onStart?.();
    const cleanup = () => {
      URL.revokeObjectURL(url);
      if (currentAudio === audio) currentAudio = null;
    };
    audio.onended = () => {
      cleanup();
      opts.onEnd?.();
    };
    audio.onerror = () => {
      cleanup();
      speakSystem(spoken, opts);
    };
    await audio.play();
  } catch {
    speakSystem(spoken, opts);
  }
}

/**
 * Speak text aloud. Resolves immediately (audio plays asynchronously); use
 * onEnd/onError for lifecycle. Returns false when no synthesis path is usable.
 */
export function speakText(text: string, opts: SpeakOptions = {}): boolean {
  const spoken = prepareSpokenText(text);
  if (!spoken) {
    opts.onEnd?.();
    return false;
  }
  stopSpeaking();
  if (opts.provider === "elevenlabs" && opts.elevenlabsAvailable) {
    void speakElevenLabs(text, spoken, opts);
    return true;
  }
  if (!isSpeechSynthesisSupported()) {
    opts.onError?.("speech_synthesis_unsupported");
    return false;
  }
  speakSystem(spoken, opts);
  return true;
}
