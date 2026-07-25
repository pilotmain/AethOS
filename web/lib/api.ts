import type { ChatProgressEvent } from "@/lib/chat/types";

const LOCAL_DEV_BASE = "http://localhost:8010";
const PILOTMAIN_API_BASE = "https://pilotmain.com/aethos-api";

function trimBase(url: string): string {
  return url.replace(/\/$/, "");
}

function localDevHostname(url: string): string | null {
  try {
    return new URL(url).hostname;
  } catch {
    return null;
  }
}

/** Resolve API origin at runtime so proxied pilotmain.com clients never hit localhost. */
export function apiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_BASE?.trim();

  if (typeof window !== "undefined") {
    const { origin, hostname } = window.location;
    if (hostname === "pilotmain.com" || hostname.endsWith(".pilotmain.com")) {
      return trimBase(`${origin}/aethos-api`);
    }
    // Local dev: UI is usually localhost:3000 while API is :8010. Browsers treat
    // localhost and 127.0.0.1 as different sites — session cookies won't cross.
    // next.config rewrites /api/v1 → API so we stay same-origin when hosts differ.
    if (process.env.NODE_ENV !== "production") {
      if (fromEnv) {
        const apiHost = localDevHostname(fromEnv);
        if (apiHost && apiHost !== hostname) {
          return trimBase(origin);
        }
        return trimBase(fromEnv);
      }
      return trimBase(origin);
    }
  }

  if (fromEnv) return trimBase(fromEnv);

  if (process.env.NODE_ENV === "production") {
    return PILOTMAIN_API_BASE;
  }

  return LOCAL_DEV_BASE;
}

/** Browser → API fetch; sends session cookie when AUTH is on (UI :3000 → API :8010). */
export async function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  return fetch(input, { ...init, credentials: "include", headers });
}

export type ChatResponse = {
  reply: string;
  intent?: string | null;
  terminal?: boolean;
  provider_stream?: boolean;
  used_llm?: boolean;
  provider?: string | null;
  model?: string | null;
  meta?: Record<string, unknown> | null;
  action?: { id: string; type?: string; lifecycle_tracked?: boolean } | null;
  job?: { id: string; type?: string; lifecycle_tracked?: boolean } | null;
};

export async function fetchChat(
  message: string,
  sessionId: string,
  interactionMode: "agent" | "chat" = "agent",
  modelOverride?: string | null,
  surface: string = "webchat",
): Promise<ChatResponse> {
  const payload: Record<string, string> = {
    message,
    session_id: sessionId,
    interaction_mode: interactionMode,
    surface,
  };
  if (modelOverride && modelOverride !== "default") {
    payload.model_override = modelOverride;
  }
  const res = await apiFetch(`${apiBase()}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Thrown when the server has streaming disabled (503) so callers can fall back. */
export class StreamingUnavailableError extends Error {}

/**
 * §2 — stream a chat turn over SSE. Calls onDelta with incremental text and
 * resolves with the final ChatResponse. Throws StreamingUnavailableError when
 * the server has streaming disabled (caller should fall back to fetchChat).
 */
export async function streamChat(
  message: string,
  sessionId: string,
  interactionMode: "agent" | "chat" = "agent",
  modelOverride: string | null | undefined,
  opts: {
    onDelta?: (text: string) => void;
    onStep?: (evt: ChatProgressEvent) => void;
    signal?: AbortSignal;
    surface?: string;
  } = {},
): Promise<ChatResponse> {
  const payload: Record<string, string> = {
    message,
    session_id: sessionId,
    interaction_mode: interactionMode,
    surface: opts.surface || "webchat",
  };
  if (modelOverride && modelOverride !== "default") {
    payload.model_override = modelOverride;
  }
  const res = await apiFetch(`${apiBase()}/api/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify(payload),
    signal: opts.signal,
  });
  if (res.status === 503) {
    throw new StreamingUnavailableError("streaming_disabled");
  }
  if (!res.ok || !res.body) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let final: ChatResponse | null = null;

  const handleEvent = (raw: string) => {
    const line = raw.split("\n").find((l) => l.startsWith("data:"));
    if (!line) return;
    const json = line.slice(5).trim();
    if (!json) return;
    let evt: {
      type?: string;
      text?: string;
      out?: ChatResponse;
      id?: string;
      tool?: string;
      action?: string;
      status?: string;
      summary?: string;
    };
    try {
      evt = JSON.parse(json);
    } catch {
      return;
    }
    if (evt.type === "delta" && evt.text) {
      opts.onDelta?.(evt.text);
    } else if (evt.type === "final" && evt.out) {
      final = evt.out;
    } else if (evt.type === "step" || evt.type === "thought") {
      // §3 — live progress narration; ignored by callers that don't opt in.
      opts.onStep?.(evt as ChatProgressEvent);
    }
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      handleEvent(buffer.slice(0, idx));
      buffer = buffer.slice(idx + 2);
    }
  }
  if (buffer.trim()) handleEvent(buffer);

  if (!final) {
    throw new Error("Stream ended without a final result.");
  }
  return final;
}

/** @deprecated use fetchChat — kept for deterministic-only tests */
export const fetchDeterministicChat = fetchChat;

export async function fetchHealth(): Promise<{
  chat_ready: boolean;
  label: string;
  panel: string;
}> {
  const { bootstrapApiConnection } = await import("@/lib/connection/bootstrapApi");
  const boot = await bootstrapApiConnection();
  if (!boot.ok) {
    throw new Error("Health check failed");
  }
  return {
    chat_ready: boot.chatReady,
    label: boot.label,
    panel: boot.panel,
  };
}
