/** Chat ↔ tracked job lifecycle bridge (polls job events, not MC). */

import { apiBase } from "@/lib/api";

import { addThreadJob, listChatThreads } from "@/lib/chat/chatThreads";
import type { CachedMessage } from "@/lib/chat/lanes";

export type JobEventType =
  | "job_created"
  | "job_started"
  | "job_progress"
  | "job_completed"
  | "job_failed"
  | "job_cancelled";

export type JobLifecycleEvent = {
  id: string;
  job_id: string;
  event_type: JobEventType;
  message: string;
  status: string;
  job_type: string;
  session_id: string;
  at: number;
};

const TRACKED_KEY = "aethos_tracked_jobs";
const SEEN_KEY = "aethos_job_events_seen";

/** Chat bubbles: one start + one terminal (skip job_created when started/completed follow). */
const CHAT_JOB_EVENT_TYPES = new Set<JobEventType>([
  "job_started",
  "job_progress",
  "job_completed",
  "job_failed",
  "job_cancelled",
]);

export function readTrackedJobIds(): string[] {
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

export function trackJobId(jobId: string): void {
  if (typeof window === "undefined" || !jobId) return;
  const ids = readTrackedJobIds();
  if (!ids.includes(jobId)) {
    ids.push(jobId);
    sessionStorage.setItem(TRACKED_KEY, JSON.stringify(ids.slice(-20)));
  }
}

export function readSeenJobEventIds(): Set<string> {
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

export function writeSeenJobEventIds(seen: Set<string>): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(SEEN_KEY, JSON.stringify([...seen].slice(-200)));
}

export type JobEventsPollResult = {
  events: JobLifecycleEvent[];
  ok: boolean;
  errorCode?: string;
};

export async function fetchJobEvents(jobIds: string[]): Promise<JobEventsPollResult> {
  if (jobIds.length === 0) return { events: [], ok: true };
  const qs = new URLSearchParams({
    ids: jobIds.join(","),
    since: "0",
  });
  let res: Response;
  try {
    res = await fetch(`${apiBase()}/api/v1/jobs/events?${qs}`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  } catch {
    return { events: [], ok: false, errorCode: "NETWORK_ERROR" };
  }
  if (!res.ok) {
    return { events: [], ok: false, errorCode: `HTTP_${res.status}` };
  }
  try {
    const data = (await res.json()) as {
      ok?: boolean;
      events?: JobLifecycleEvent[];
      error?: { code?: string };
    };
    if (data.ok === false) {
      return { events: [], ok: false, errorCode: data.error?.code ?? "EVENT_POLL_FAILED" };
    }
    const events = Array.isArray(data.events) ? data.events : [];
    return {
      events: events.filter((e) => CHAT_JOB_EVENT_TYPES.has(e.event_type)),
      ok: true,
    };
  } catch {
    return { events: [], ok: false, errorCode: "PARSE_ERROR" };
  }
}

export function lifecycleMessageToJobChatEvent(event: JobLifecycleEvent): CachedMessage {
  return {
    id: `jevt-${event.id}`,
    role: "system",
    content: event.message,
    event_type: event.event_type,
    action_id: event.job_id,
  };
}

export function mergeJobLifecycleEvents(
  messages: CachedMessage[],
  events: JobLifecycleEvent[],
  seen: Set<string>,
): { messages: CachedMessage[]; seen: Set<string>; added: number } {
  const next = [...messages];
  const seenNext = new Set(seen);
  let added = 0;
  for (const event of events) {
    const bubble = lifecycleMessageToJobChatEvent(event);
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

export function pruneSeenJobToDisplayed(messages: CachedMessage[], seen: Set<string>): Set<string> {
  const displayed = new Set(
    messages
      .filter((m) => m.role === "system" && m.id.startsWith("jevt-"))
      .map((m) => m.id.replace(/^jevt-/, "")),
  );
  return new Set([...seen].filter((id) => displayed.has(id)));
}

export function extractJobId(text: string): string | null {
  const m = text.match(/`(job-[a-f0-9]+)`/i) || text.match(/\b(job-[a-f0-9]+)\b/i);
  return m ? m[1] : null;
}

/** Detach a terminal job and any linked preflight parent from thread busy tracking. */
export async function detachTerminalJobFromThreads(jobId: string): Promise<void> {
  if (!jobId) return;
  const { removeThreadJob } = await import("@/lib/chat/chatThreads");
  removeThreadJob(jobId);
  try {
    const { apiBase, apiFetch } = await import("@/lib/api");
    const res = await apiFetch(`${apiBase()}/api/v1/jobs/${encodeURIComponent(jobId)}`);
    if (!res.ok) return;
    const data = (await res.json()) as { job?: { params?: Record<string, unknown> } };
    const params = data.job?.params;
    if (!params || typeof params !== "object") return;
    const parent = params.parent_greenfield_job_id;
    if (typeof parent === "string" && parent) removeThreadJob(parent);
    const orch = params.orchestration_job_id;
    if (typeof orch === "string" && orch) removeThreadJob(orch);
  } catch {
    /* best-effort */
  }
}

export function registerProposedJobFromMeta(
  meta: Record<string, unknown> | null | undefined,
  reply: string,
): string | null {
  const jobObj = meta?.job;
  const fromJob =
    jobObj &&
    typeof jobObj === "object" &&
    !Array.isArray(jobObj) &&
    typeof (jobObj as { id?: string }).id === "string"
      ? (jobObj as { id: string }).id
      : null;
  const fromMeta =
    meta && typeof meta.proposed_job_id === "string" ? meta.proposed_job_id : null;
  const fromReply = extractJobId(reply);
  const orchestrationId =
    meta && typeof meta.orchestration_job_id === "string" ? meta.orchestration_job_id : null;
  const id = fromJob || fromMeta || orchestrationId || fromReply;

  const bulkIds =
    meta && typeof meta.proposed_job_ids === "string"
      ? meta.proposed_job_ids.split(",").map((s) => s.trim()).filter(Boolean)
      : [];
  for (const jobId of bulkIds) trackJobId(jobId);

  const replyIds = [...reply.matchAll(/\b(job-[a-f0-9]+)\b/gi)].map((m) => m[1]);
  for (const jobId of replyIds) trackJobId(jobId);

  if (orchestrationId) trackJobId(orchestrationId);

  if (id) trackJobId(id);
  return orchestrationId || id;
}

/** Track a durable job for lifecycle polling and attach it to the chat thread for session_id. */
export function attachJobToChatSession(sessionId: string, jobId: string): void {
  if (!jobId) return;
  trackJobId(jobId);
  if (typeof window === "undefined") return;
  const thread = listChatThreads().find((t) => t.sessionId === sessionId);
  if (thread) addThreadJob(thread.id, jobId);
}
