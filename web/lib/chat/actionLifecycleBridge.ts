/** Chat ↔ runtime action lifecycle bridge (polls authority events, not MC). */

import { apiBase } from "@/lib/api";
import { getActiveSessionId } from "@/lib/chat/chatThreads";

import type { CachedMessage } from "@/lib/chat/types";

export type ActionEventType =
  | "action_approved"
  | "action_completed"
  | "action_failed"
  | "action_denied";

export type ActionLifecycleEvent = {
  id: string;
  action_id: string;
  event_type: ActionEventType;
  message: string;
  status: string;
  action_type: string;
  session_id: string;
  at: number;
  browser_session_id?: string;
};

const TRACKED_KEY = "aethos_tracked_actions";
const SEEN_KEY = "aethos_action_events_seen";

export function extractActionId(text: string): string | null {
  const m = text.match(/`(act-[a-f0-9]+)`/i) || text.match(/\b(act-[a-f0-9]+)\b/i);
  return m ? m[1] : null;
}

export function readTrackedActionIds(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = sessionStorage.getItem(TRACKED_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as string[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function trackActionId(actionId: string): void {
  if (typeof window === "undefined" || !actionId) return;
  const ids = readTrackedActionIds();
  if (!ids.includes(actionId)) {
    ids.push(actionId);
    sessionStorage.setItem(TRACKED_KEY, JSON.stringify(ids.slice(-20)));
  }
}

export function readSeenEventIds(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = sessionStorage.getItem(SEEN_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw) as string[];
    return new Set(Array.isArray(parsed) ? parsed : []);
  } catch {
    return new Set();
  }
}

export function writeSeenEventIds(seen: Set<string>): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(SEEN_KEY, JSON.stringify([...seen].slice(-200)));
}

export async function fetchActionEvents(actionIds: string[]): Promise<ActionLifecycleEvent[]> {
  if (actionIds.length === 0) return [];
  const qs = new URLSearchParams({
    ids: actionIds.join(","),
    since: "0",
  });
  const res = await fetch(`${apiBase()}/api/v1/actions/events?${qs}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return [];
  const data = (await res.json()) as { events?: ActionLifecycleEvent[] };
  return Array.isArray(data.events) ? data.events : [];
}

export function lifecycleMessageToChatEvent(
  event: ActionLifecycleEvent,
): CachedMessage {
  return {
    id: `evt-${event.id}`,
    role: "system",
    content: event.message,
    event_type: event.event_type,
    action_id: event.action_id,
  };
}

export function mergeLifecycleEvents(
  messages: CachedMessage[],
  events: ActionLifecycleEvent[],
  seen: Set<string>,
): { messages: CachedMessage[]; seen: Set<string>; added: number } {
  const next = [...messages];
  const seenNext = new Set(seen);
  let added = 0;
  for (const event of events) {
    const bubble = lifecycleMessageToChatEvent(event);
    if (next.some((m) => m.id === bubble.id)) {
      seenNext.add(event.id);
      continue;
    }
    if (seenNext.has(event.id)) continue;
    seenNext.add(event.id);
    next.push(bubble);
    added += 1;
  }
  return { messages: next, seen: seenNext, added };
}

/** Drop stale seen markers that never produced a visible bubble (React strict-mode safe). */
export function pruneSeenToDisplayed(messages: CachedMessage[], seen: Set<string>): Set<string> {
  const displayed = new Set(
    messages
      .filter((m) => m.role === "system" && m.id.startsWith("evt-"))
      .map((m) => m.id.replace(/^evt-/, "")),
  );
  return new Set([...seen].filter((id) => displayed.has(id)));
}

export function registerProposedActionFromMeta(
  meta: Record<string, unknown> | null | undefined,
  reply: string,
): string | null {
  const actionObj = meta?.action;
  const fromAction =
    actionObj &&
    typeof actionObj === "object" &&
    !Array.isArray(actionObj) &&
    typeof (actionObj as { id?: string }).id === "string"
      ? (actionObj as { id: string }).id
      : null;
  const fromMeta =
    meta && typeof meta.proposed_action_id === "string" ? meta.proposed_action_id : null;
  const fromReply = extractActionId(reply);
  const id = fromAction || fromMeta || fromReply;
  if (id) trackActionId(id);
  return id;
}


export function getOrCreateChatSessionId(): string {
  if (typeof window === "undefined") return "default";
  try {
    return getActiveSessionId();
  } catch {
    return "default";
  }
}
