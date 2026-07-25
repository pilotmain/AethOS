/** Chat ↔ browser session lifecycle (polls stored session events, deduped). */

import { apiBase } from "@/lib/api";

import type { CachedMessage } from "@/lib/chat/lanes";

import type { BrowserSessionEventRecord } from "@/lib/missionControl/browserSessions";

const TRACKED_KEY = "aethos_tracked_browser_sessions";
const SEEN_KEY = "aethos_browser_events_seen";
const CURSOR_KEY = "aethos_browser_events_cursor";

/**
 * Chat milestones from action approve/complete — not re-polled from browser events.
 * Browser poller handles terminal / operator-wait updates only.
 */
const CHAT_BROWSER_EVENT_TYPES = new Set([
  "session_waiting_for_operator",
  "session_completed",
  "session_failed",
  "session_cancelled",
  "session_timed_out",
]);

export function readTrackedBrowserSessionIds(): string[] {
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

export function trackBrowserSessionId(sessionId: string): void {
  if (typeof window === "undefined" || !sessionId) return;
  const ids = readTrackedBrowserSessionIds();
  if (!ids.includes(sessionId)) {
    ids.push(sessionId);
    sessionStorage.setItem(TRACKED_KEY, JSON.stringify(ids.slice(-20)));
  }
}

export function registerBrowserSessionFromMeta(meta: Record<string, unknown> | undefined): void {
  const raw = meta?.browser_session_id;
  const sid = typeof raw === "string" ? raw.trim() : "";
  if (sid.startsWith("bsess-")) {
    trackBrowserSessionId(sid);
  }
}

export function trackBrowserSessionFromActionEvent(event: {
  browser_session_id?: string;
}): void {
  const sid = event.browser_session_id?.trim();
  if (sid?.startsWith("bsess-")) {
    trackBrowserSessionId(sid);
  }
}

export function readSeenBrowserEventIds(): Set<string> {
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

export function writeSeenBrowserEventIds(seen: Set<string>): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(SEEN_KEY, JSON.stringify([...seen].slice(-200)));
}

export function readBrowserEventsCursor(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(CURSOR_KEY);
  } catch {
    return null;
  }
}

export function writeBrowserEventsCursor(eventId: string): void {
  if (typeof window === "undefined" || !eventId) return;
  sessionStorage.setItem(CURSOR_KEY, eventId);
}

export function browserEventDedupeKey(event: BrowserSessionEventRecord): string {
  return event.id || `${event.session_id}:${event.event_type}`;
}

export function browserEventBubbleId(event: BrowserSessionEventRecord): string {
  return `bsess-evt-${browserEventDedupeKey(event)}`;
}

export async function fetchBrowserSessionEvents(
  sessionIds: string[],
  options?: { sinceEventId?: string | null },
): Promise<BrowserSessionEventRecord[]> {
  if (sessionIds.length === 0) return [];
  const qs = new URLSearchParams({ ids: sessionIds.join(","), since: "0" });
  const cursor = options?.sinceEventId ?? readBrowserEventsCursor();
  if (cursor) {
    qs.set("since_event_id", cursor);
  }
  const res = await fetch(`${apiBase()}/api/v1/browser/sessions/events?${qs}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return [];
  const body = (await res.json()) as { events?: BrowserSessionEventRecord[] };
  const events = body.events ?? [];
  return events.filter((e) => CHAT_BROWSER_EVENT_TYPES.has(e.event_type));
}

export function mergeBrowserLifecycleEvents(
  messages: CachedMessage[],
  events: BrowserSessionEventRecord[],
  seen: Set<string>,
): { messages: CachedMessage[]; seen: Set<string>; added: number } {
  const out = [...messages];
  const nextSeen = new Set(seen);
  let added = 0;
  let lastEventId: string | null = null;
  for (const event of events) {
    if (!CHAT_BROWSER_EVENT_TYPES.has(event.event_type)) continue;
    const dedupeKey = browserEventDedupeKey(event);
    const compositeKey = `${event.session_id}:${event.event_type}`;
    if (nextSeen.has(dedupeKey) || nextSeen.has(compositeKey)) continue;
    const bubbleId = browserEventBubbleId(event);
    if (out.some((m) => m.id === bubbleId)) {
      nextSeen.add(dedupeKey);
      nextSeen.add(compositeKey);
      continue;
    }
    nextSeen.add(dedupeKey);
    nextSeen.add(compositeKey);
    out.push({
      id: bubbleId,
      role: "system",
      content: event.message,
    });
    added += 1;
    lastEventId = event.id;
  }
  if (lastEventId) {
    writeBrowserEventsCursor(lastEventId);
  }
  return { messages: out, seen: nextSeen, added };
}

/** Drop stale seen markers that never produced a visible bubble (React strict-mode safe). */
export function pruneSeenBrowserToDisplayed(
  messages: CachedMessage[],
  seen: Set<string>,
): Set<string> {
  const displayed = new Set(
    messages
      .filter((m) => m.role === "system" && m.id.startsWith("bsess-evt-"))
      .map((m) => m.id.replace(/^bsess-evt-/, "")),
  );
  return new Set([...seen].filter((id) => displayed.has(id) || !id.includes(":")));
}
