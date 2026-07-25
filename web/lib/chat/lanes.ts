/** Client mirror of aethos_core/chat/lanes.py + deterministic.py (MVP subset). */

const CAPABILITY_RX =
  /^(what can you do|what do you do|who are you|what are you capable|capabilities)\b/i;
const VERCEL_RX = /\bvercel\.com\b|\bvercel\b/i;
const LOGIN_RX = /\b(log\s*in\s+to|login\s+to|sign\s+in\s+to)\b/i;
const CONFIG_RX =
  /\b(what model|which model|runtime config|anthropic model|openai model|claude model|gpt model|which llm|what llm|environment variable|\.env\b)/i;

export function isRuntimeConfigQuestion(text: string): boolean {
  const raw = text.trim();
  if (!raw) return false;
  if (/\bblind\s+model\s+eval\b/i.test(raw)) return false;
  if (CONFIG_RX.test(raw)) return true;
  return (
    /\bmodel\b/i.test(raw) &&
    /\b(using|configured|active|check|which|what|tell|show|provider|anthropic|claude|openai|gpt|llm|runtime)\b/i.test(raw)
  );
}
const TERMINAL_RX = /\b(can you access terminal|access terminal|host executor)\b/i;
const RUNTIME_STATUS_RX = /\b(runtime status|show system status|system status)\b/i;
const PROJECT_TEMPLATE_RX =
  /\b(explain|describe)\b.*\baethos\b.*\barchitecture\b|\bmvp roadmap\b|\bbuild first\b|\bfast and reliable\b|\bmission control\b|\bwhat makes aethos\b.*\b(different|unique)\b|\bwhy aethos\b|\bmakes\b.*\baethos\b.*\bdifferent\b|\bsummarize.*project direction\b|\btest checklist\b|\bwhat should we do next\b|\bwhat happens if.*anthropic\b|\brestart aethos\b|\bbrowser automation\b|\bchannels should.*support\b/i;

export function shouldUseDeterministicLane(text: string): boolean {
  const raw = text.trim();
  if (!raw) return false;
  if (/^(hi|hello|hey)\b/i.test(raw)) return true;
  if (CAPABILITY_RX.test(raw)) return true;
  if (CONFIG_RX.test(raw) || isRuntimeConfigQuestion(raw)) return true;
  if (TERMINAL_RX.test(raw)) return true;
  if (RUNTIME_STATUS_RX.test(raw)) return true;
  if (PROJECT_TEMPLATE_RX.test(raw)) return true;
  if (VERCEL_RX.test(raw) && LOGIN_RX.test(raw)) return true;
  if (/\bwhat do you need from me\b/i.test(raw)) return true;
  if (/\bhow (?:do i|to) set up\b/i.test(raw)) return true;
  if (/\bcan you deploy\b.*\bvercel\b/i.test(raw)) return true;
  if (/\bcan you login to websites\b/i.test(raw)) return true;
  return false;
}

export function isPanelDegradedCopy(message: string): boolean {
  return /panel degraded|panels may still work|panel is slow to load/i.test(message);
}

export function formatChatError(message: string): string {
  if (/failed to fetch/i.test(message)) {
    return (
      "AethOS API connection dropped during this operation. " +
      "Your saved session and job may still be on the server — check Mission Control → Jobs, then retry."
    );
  }
  if (isPanelDegradedCopy(message)) {
    return "Chat could not finish this turn. Your message was kept — try again.";
  }
  return message || "Chat request failed";
}

import type { CachedMessage } from "@/lib/chat/types";
import { getActiveThread, updateActiveThreadMessages } from "@/lib/chat/chatThreads";

export type { CachedMessage } from "@/lib/chat/types";

export function readCachedMessages(): CachedMessage[] {
  if (typeof window === "undefined") return [];
  try {
    return getActiveThread().messages;
  } catch {
    return [];
  }
}

export function writeCachedMessages(messages: CachedMessage[]): void {
  if (typeof window === "undefined") return;
  try {
    updateActiveThreadMessages(messages);
  } catch {
    /* quota */
  }
}
