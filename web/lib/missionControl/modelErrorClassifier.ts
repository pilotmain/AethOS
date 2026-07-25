/** Classify a model-call failure into an honest, user-facing hint.
 *
 * Distinguishes AethOS config problems (no key) from the user's provider account
 * problems (402 billing, 429 quota) and transient outages — so a 429/402 reads as
 * "your provider account", not an AethOS bug. Raw text stays available for debug. */

export type ModelFailureTone = "config" | "account" | "transient" | "error";

export type ModelFailure = {
  tone: ModelFailureTone;
  hint: string;
  raw: string;
};

export function classifyModelError(raw: string | null | undefined): ModelFailure {
  const text = raw ?? "";
  const low = text.toLowerCase();

  if (low.includes("not configured") || low.includes("add a key")) {
    return {
      tone: "config",
      hint: "Not configured — add a key in Mission Control → Connections.",
      raw: text,
    };
  }
  if (low.includes("402") || low.includes("payment required") || low.includes("insufficient") || low.includes("credit")) {
    return {
      tone: "account",
      hint: "Provider account needs credits/billing — add credits in your provider account.",
      raw: text,
    };
  }
  if (low.includes("429") || low.includes("too many requests") || low.includes("rate limit") || low.includes("quota")) {
    return {
      tone: "account",
      hint: "Rate-limited / quota exceeded — check your provider billing & limits.",
      raw: text,
    };
  }
  if (low.includes("401") || low.includes("403") || low.includes("unauthorized") || low.includes("forbidden") || low.includes("invalid api key")) {
    return {
      tone: "config",
      hint: "Key rejected — re-add it in Mission Control → Connections.",
      raw: text,
    };
  }
  if (low.includes("timeout") || low.includes("timed out") || low.includes("unavailable") || low.includes("connection")) {
    return {
      tone: "transient",
      hint: "Provider temporarily unavailable — retry.",
      raw: text,
    };
  }
  return { tone: "error", hint: text || "Request failed.", raw: text };
}

export function toneColor(tone: ModelFailureTone): string {
  switch (tone) {
    case "account":
      return "var(--aethos-warn)";
    case "transient":
      return "var(--aethos-accent)";
    case "config":
      return "var(--aethos-danger)";
    default:
      return "var(--aethos-danger)";
  }
}
