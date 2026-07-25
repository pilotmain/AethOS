/**
 * Browser speech-to-text via the Web Speech API (SpeechRecognition). Local-first
 * and zero-dependency: transcription happens in the browser. We degrade
 * gracefully when the API is missing (see isSpeechRecognitionSupported).
 *
 * The Web Speech API is not in the standard TS DOM lib, so the minimal shapes we
 * use are declared here.
 */

type SpeechRecognitionAlternativeLike = { transcript: string; confidence: number };
type SpeechRecognitionResultLike = {
  readonly length: number;
  readonly isFinal: boolean;
  item(index: number): SpeechRecognitionAlternativeLike;
  [index: number]: SpeechRecognitionAlternativeLike;
};
type SpeechRecognitionResultListLike = {
  readonly length: number;
  item(index: number): SpeechRecognitionResultLike;
  [index: number]: SpeechRecognitionResultLike;
};
type SpeechRecognitionEventLike = {
  readonly resultIndex: number;
  readonly results: SpeechRecognitionResultListLike;
};
type SpeechRecognitionErrorEventLike = { readonly error: string };

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
};

type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

function getRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export function isSpeechRecognitionSupported(): boolean {
  return getRecognitionCtor() !== null;
}

export type RecognizerCallbacks = {
  /** Fired continuously with the best-effort transcript so far (interim + final). */
  onTranscript?: (text: string, isFinal: boolean) => void;
  onError?: (error: string) => void;
  onEnd?: () => void;
  onStart?: () => void;
};

export type RecognizerHandle = {
  start: () => void;
  stop: () => void;
  abort: () => void;
};

/**
 * Create a recognizer. `continuous` keeps the mic open (talk/wake mode); the
 * default single-shot mode captures one utterance for push-to-talk.
 */
export function createSpeechRecognizer(
  callbacks: RecognizerCallbacks,
  opts: { lang?: string; continuous?: boolean; interimResults?: boolean } = {},
): RecognizerHandle | null {
  const Ctor = getRecognitionCtor();
  if (!Ctor) return null;
  const recognition = new Ctor();
  recognition.lang = opts.lang || (typeof navigator !== "undefined" ? navigator.language : "en-US") || "en-US";
  recognition.continuous = Boolean(opts.continuous);
  recognition.interimResults = opts.interimResults !== false;
  recognition.maxAlternatives = 1;

  recognition.onresult = (event) => {
    let interim = "";
    let finalText = "";
    for (let i = event.resultIndex; i < event.results.length; i += 1) {
      const result = event.results[i];
      const alt = result[0];
      if (!alt) continue;
      if (result.isFinal) finalText += alt.transcript;
      else interim += alt.transcript;
    }
    const combined = (finalText || interim).trim();
    if (combined) callbacks.onTranscript?.(combined, Boolean(finalText));
  };
  recognition.onerror = (event) => callbacks.onError?.(event.error || "speech_error");
  recognition.onend = () => callbacks.onEnd?.();
  recognition.onstart = () => callbacks.onStart?.();

  let active = false;
  return {
    start: () => {
      if (active) return;
      active = true;
      try {
        recognition.start();
      } catch {
        active = false;
      }
    },
    stop: () => {
      active = false;
      try {
        recognition.stop();
      } catch {
        /* already stopped */
      }
    },
    abort: () => {
      active = false;
      try {
        recognition.abort();
      } catch {
        /* already stopped */
      }
    },
  };
}
