"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchVoiceConfig, type VoiceConfig } from "@/lib/voice/voiceConfig";
import {
  createSpeechRecognizer,
  isSpeechRecognitionSupported,
  type RecognizerHandle,
} from "@/lib/voice/speechRecognition";
import { isMediaRecorderSupported, startMediaRecorderCapture, type RecorderHandle } from "@/lib/voice/mediaRecorderCapture";
import { transcribeAudioBlob } from "@/lib/voice/whisperTranscribe";
import {
  isSpeechSynthesisSupported,
  listSpeechVoices,
  onVoicesChanged,
  pickDefaultVoiceURI,
  speakText,
  stopSpeaking as stopSpeakingNow,
  type SpeechVoice,
} from "@/lib/voice/speechSynthesis";

export type TranscriptHandler = (text: string, opts: { autoSend: boolean }) => void;

export type VoiceController = {
  config: VoiceConfig | null;
  sttSupported: boolean;
  ttsSupported: boolean;
  listening: boolean;
  talkMode: boolean;
  speakReplies: boolean;
  speaking: boolean;
  interim: string;
  error: string | null;
  /** Push-to-talk: capture one utterance into the composer (user confirms/sends). */
  toggleListening: () => void;
  /** Hands-free talk mode (wake phrase → auto-send → spoken reply → keep listening). */
  toggleTalkMode: () => void;
  toggleSpeakReplies: () => void;
  /** Speak an assistant reply when output is enabled and replies are unmuted. */
  speakReply: (text: string, opts?: { force?: boolean }) => void;
  stopSpeaking: () => void;
  clearError: () => void;
  /** Honest reason the mic can't be used right now (disabled / unsupported), or null. */
  micDisabledReason: () => string | null;
  /** Re-fetch voice config (e.g. after saving wake-phrase / send-mode preferences). */
  reloadConfig: () => void;
  /** Available system voices (male/female/accent) for spoken replies. */
  voices: SpeechVoice[];
  /** The selected voice (voiceURI), or "" for the browser default. */
  voiceURI: string;
  setVoiceURI: (uri: string) => void;
};

export function useVoice(onTranscript: TranscriptHandler): VoiceController {
  const [config, setConfig] = useState<VoiceConfig | null>(null);
  const [listening, setListening] = useState(false);
  const [talkMode, setTalkMode] = useState(false);
  const [speakReplies, setSpeakReplies] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [voices, setVoices] = useState<SpeechVoice[]>([]);
  const [voiceURI, setVoiceURIState] = useState("");
  const voiceURIRef = useRef("");
  voiceURIRef.current = voiceURI;
  const voicesRef = useRef<SpeechVoice[]>([]);
  voicesRef.current = voices;

  const sttSupported = isSpeechRecognitionSupported();
  const ttsSupported = isSpeechSynthesisSupported();

  const pushRecognizerRef = useRef<RecognizerHandle | null>(null);
  const whisperRecorderRef = useRef<RecorderHandle | null>(null);
  const talkRecognizerRef = useRef<RecognizerHandle | null>(null);
  const talkModeRef = useRef(false);
  const speakingRef = useRef(false);
  // Two-step wake: true after the wake phrase is heard alone, so the NEXT utterance
  // (without repeating the phrase) becomes the command.
  const armedRef = useRef(false);
  const onTranscriptRef = useRef(onTranscript);
  onTranscriptRef.current = onTranscript;
  const configRef = useRef<VoiceConfig | null>(null);
  configRef.current = config;

  useEffect(() => {
    let cancelled = false;
    void fetchVoiceConfig().then((cfg) => {
      if (cancelled) return;
      setConfig(cfg);
      // Spoken replies: remember the user's choice across reloads; default ON when output
      // is enabled so they don't have to re-toggle it every session.
      let pref: string | null = null;
      try {
        pref = window.localStorage.getItem("aethos.voice.speakReplies");
      } catch {
        pref = null;
      }
      setSpeakReplies(pref === null ? cfg.outputEnabled : pref === "1");
    });
    return () => {
      cancelled = true;
      pushRecognizerRef.current?.abort();
      whisperRecorderRef.current?.abort();
      talkRecognizerRef.current?.abort();
      stopSpeakingNow();
    };
  }, []);

  // Remember the spoken-replies choice across sessions.
  useEffect(() => {
    try {
      window.localStorage.setItem("aethos.voice.speakReplies", speakReplies ? "1" : "0");
    } catch {
      /* ignore */
    }
  }, [speakReplies]);

  // Load available system voices (male/female/accent) and the user's saved choice.
  useEffect(() => {
    const refresh = () => setVoices(listSpeechVoices());
    refresh();
    const unsub = onVoicesChanged(refresh);
    try {
      const saved = window.localStorage.getItem("aethos.voice.voiceURI");
      if (saved) setVoiceURIState(saved);
    } catch {
      /* ignore */
    }
    return unsub;
  }, []);

  const setVoiceURI = useCallback((uri: string) => {
    setVoiceURIState(uri);
    try {
      window.localStorage.setItem("aethos.voice.voiceURI", uri);
    } catch {
      /* ignore */
    }
  }, []);

  // ---- push-to-talk (§1) ----------------------------------------------------
  const stopListening = useCallback(() => {
    const whisperRecorder = whisperRecorderRef.current;
    whisperRecorderRef.current = null;
    if (whisperRecorder) {
      void whisperRecorder.stop().then((blob) => {
        if (!blob) {
          setListening(false);
          setInterim("");
          return;
        }
        setInterim("Transcribing…");
        void transcribeAudioBlob(blob).then((text) => {
          setInterim("");
          setListening(false);
          if (text) onTranscriptRef.current(text, { autoSend: Boolean(configRef.current?.autoSend) });
          else setError("Could not transcribe audio — try again or switch to browser STT.");
        });
      });
      return;
    }
    pushRecognizerRef.current?.stop();
    pushRecognizerRef.current = null;
    setListening(false);
    setInterim("");
  }, []);

  const startListening = useCallback(() => {
    const cfg = configRef.current;
    if (!cfg?.inputEnabled) {
      setError(
        cfg && cfg.surfaceEnabled
          ? "Voice input is off — enable VOICE_INPUT_ENABLED."
          : "Voice is disabled — enable VOICE_SURFACE_ENABLED to talk to AethOS.",
      );
      return;
    }
    const useWhisper = cfg.sttProvider === "whisper" && cfg.whisperAvailable;
    if (useWhisper) {
      if (!isMediaRecorderSupported()) {
        setError("Your browser can't capture audio for Whisper transcription.");
        return;
      }
      setError(null);
      void startMediaRecorderCapture().then((handle) => {
        if (!handle) {
          setError("Microphone access was blocked or unavailable.");
          return;
        }
        whisperRecorderRef.current = handle;
        setListening(true);
        setInterim("Listening…");
      });
      return;
    }
    if (!sttSupported) {
      setError("Your browser doesn't support voice input.");
      return;
    }
    setError(null);
    const handle = createSpeechRecognizer(
      {
        onTranscript: (text, isFinal) => {
          setInterim(text);
          if (isFinal) {
            onTranscriptRef.current(text, { autoSend: Boolean(configRef.current?.autoSend) });
            stopListening();
          }
        },
        onError: (err) => {
          if (err !== "no-speech" && err !== "aborted") setError(`Voice input error: ${err}`);
          stopListening();
        },
        onEnd: () => setListening(false),
      },
      { continuous: false, interimResults: true },
    );
    if (!handle) {
      setError("Your browser doesn't support voice input.");
      return;
    }
    pushRecognizerRef.current = handle;
    handle.start();
    setListening(true);
  }, [sttSupported, stopListening]);

  const toggleListening = useCallback(() => {
    if (listening) stopListening();
    else startListening();
  }, [listening, startListening, stopListening]);

  // ---- spoken replies (§2) --------------------------------------------------
  const stopSpeaking = useCallback(() => {
    stopSpeakingNow();
    speakingRef.current = false;
    setSpeaking(false);
    // In talk mode, resume listening once we stop speaking.
    if (talkModeRef.current) talkRecognizerRef.current?.start();
  }, []);

  const speakReply = useCallback(
    (text: string, opts: { force?: boolean } = {}) => {
      const cfg = configRef.current;
      if (!cfg?.outputEnabled) return;
      if (!opts.force && !speakReplies) return;
      // Avoid the mic hearing our own voice: pause talk-mode capture while speaking.
      if (talkModeRef.current) talkRecognizerRef.current?.stop();
      speakingRef.current = true;
      setSpeaking(true);
      speakText(text, {
        provider: cfg.ttsProvider,
        elevenlabsAvailable: cfg.elevenlabsAvailable,
        voiceURI: voiceURIRef.current || pickDefaultVoiceURI(voicesRef.current) || undefined,
        onEnd: () => {
          speakingRef.current = false;
          setSpeaking(false);
          if (talkModeRef.current) talkRecognizerRef.current?.start();
        },
        onError: (err) => {
          speakingRef.current = false;
          setSpeaking(false);
          if (err === "speech_synthesis_unsupported") setError("This browser can't speak replies.");
          if (talkModeRef.current) talkRecognizerRef.current?.start();
        },
      });
    },
    [speakReplies],
  );
  // Stable handle so the talk-mode closure can speak the wake greeting without going stale.
  const speakReplyRef = useRef(speakReply);
  speakReplyRef.current = speakReply;

  const toggleSpeakReplies = useCallback(() => {
    setSpeakReplies((prev) => {
      if (prev) stopSpeakingNow();
      return !prev;
    });
  }, []);

  // ---- talk mode + wake phrase (§3) -----------------------------------------
  const stopTalkMode = useCallback(() => {
    talkModeRef.current = false;
    armedRef.current = false;
    talkRecognizerRef.current?.abort();
    talkRecognizerRef.current = null;
    setTalkMode(false);
    setInterim("");
  }, []);

  const startTalkMode = useCallback(() => {
    const cfg = configRef.current;
    if (!cfg?.wakeEnabled) {
      setError(
        cfg && cfg.surfaceEnabled
          ? "Talk mode is off — enable VOICE_WAKE_ENABLED."
          : "Voice is disabled — enable VOICE_SURFACE_ENABLED.",
      );
      return;
    }
    if (!sttSupported) {
      setError("Your browser doesn't support voice input.");
      return;
    }
    setError(null);
    const phrase = (cfg.wakePhrase || "hey aethos").toLowerCase();
    const handle = createSpeechRecognizer(
      {
        onTranscript: (text, isFinal) => {
          setInterim(armedRef.current ? `🎧 ${text}` : text);
          if (!isFinal) return;
          // Tolerant wake match: ignore punctuation/spacing so STT quirks
          // ("hey, ethos" / "hey aythos") still trigger the configured phrase.
          const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9 ]/g, "").replace(/\s+/g, " ").trim();
          const nText = norm(text);
          const nPhrase = norm(phrase);
          const idx = nPhrase ? nText.indexOf(nPhrase) : -1;
          // Stop/sleep phrases end the hands-free conversation (back to needing the wake word).
          const STOP_RX = /\b(stop listening|stop talking|that'?s all|that is all|never mind|nevermind|we'?re done|go to sleep|cancel that|dismiss|goodbye)\b/i;
          // Once armed, stay in conversation — every utterance is a command, no re-wake needed.
          const send = (cmd: string) => {
            setInterim(armedRef.current ? "🎧 Listening…" : "");
            if (cmd) onTranscriptRef.current(cmd, { autoSend: configRef.current?.autoSend !== false });
          };

          if (idx !== -1) {
            const command = nText.slice(idx + nPhrase.length).replace(/^[\s,.:!?-]+/, "").trim();
            const firstWake = !armedRef.current;
            armedRef.current = true; // enter / stay in conversation mode
            if (command) {
              send(command);
            } else {
              setInterim("🎧 Listening — say your request…");
              if (firstWake) {
                const who = (configRef.current?.operatorName || "").trim();
                const greeting = who
                  ? `Welcome back, ${who} — what can I do for you?`
                  : "Welcome back — what can I do for you?";
                speakReplyRef.current(greeting, { force: true });
              }
            }
            return;
          }

          // No wake phrase this utterance.
          if (armedRef.current) {
            const t = text.trim();
            if (STOP_RX.test(norm(t))) {
              armedRef.current = false;
              setInterim("");
              speakReplyRef.current("Okay — say the wake word when you need me.", { force: true });
              return;
            }
            send(t); // conversation continues without repeating the wake word
            return;
          }
          setInterim("");
        },
        onError: (err) => {
          if (err === "not-allowed" || err === "service-not-allowed") {
            setError("Microphone access was blocked.");
            stopTalkMode();
          }
        },
        onEnd: () => {
          // Browsers end continuous recognition on silence; keep listening unless
          // we're mid-speech or the user turned talk mode off.
          if (talkModeRef.current && !speakingRef.current) talkRecognizerRef.current?.start();
        },
      },
      { continuous: true, interimResults: true },
    );
    if (!handle) {
      setError("Your browser doesn't support voice input.");
      return;
    }
    talkRecognizerRef.current = handle;
    talkModeRef.current = true;
    handle.start();
    setTalkMode(true);
  }, [sttSupported, stopTalkMode]);

  const toggleTalkMode = useCallback(() => {
    if (talkModeRef.current) stopTalkMode();
    else startTalkMode();
  }, [startTalkMode, stopTalkMode]);

  const clearError = useCallback(() => setError(null), []);

  const micDisabledReason = useCallback((): string | null => {
    const cfg = configRef.current;
    if (!cfg) return null;
    if (!cfg.surfaceEnabled) return "Voice is disabled — enable VOICE_SURFACE_ENABLED to talk to AethOS.";
    if (!cfg.inputEnabled) return "Voice input is off — enable VOICE_INPUT_ENABLED.";
    if (!sttSupported) return "Your browser doesn't support voice input.";
    return null;
  }, [sttSupported]);

  return {
    config,
    sttSupported,
    ttsSupported,
    listening,
    talkMode,
    speakReplies,
    speaking,
    interim,
    error,
    toggleListening,
    toggleTalkMode,
    toggleSpeakReplies,
    speakReply,
    stopSpeaking,
    clearError,
    micDisabledReason,
    reloadConfig: () => {
      void fetchVoiceConfig().then(setConfig);
    },
    voices,
    voiceURI,
    setVoiceURI,
  };
}
