/** Supervised browser sessions — Mission Control Browser tab. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type BrowserSessionRecord = {
  id: string;
  target: string;
  url: string;
  status: string;
  mode?: string;
  error?: string | null;
  operator_approved?: boolean;
  created_at?: number;
  started_at?: number | null;
  last_heartbeat?: number;
  heartbeat_age_sec?: number | null;
  browser_pid?: number | null;
  duration_sec?: number | null;
  chat_session_id?: string;
  profile_save_eligible?: boolean;
  storage_state_available?: boolean;
  persistence_status?: string;
  persistence_last_attempt_at?: number | null;
  persistence_last_error?: string | null;
};

export type BrowserSessionEventRecord = {
  id: string;
  session_id: string;
  event_type: string;
  message: string;
  status: string;
  target: string;
  chat_session_id: string;
  at: number;
};

export type BrowserSessionsResponse = {
  sessions: BrowserSessionRecord[];
  count: number;
  active_session: BrowserSessionRecord | null;
  active_sessions: BrowserSessionRecord[];
  active_session_count: number;
};

export type BrowserStatusResponse = {
  enabled: boolean;
  available: boolean;
  active_session?: BrowserSessionRecord | null;
  active_session_count?: number;
  browser_capability?: unknown;
};

export const fetchBrowserStatus = () => mcFetch<BrowserStatusResponse>("/api/v1/browser/status");

export const fetchBrowserSessions = () => mcFetch<BrowserSessionsResponse>("/api/v1/browser/sessions");

export const fetchBrowserSessionEvents = (sessionIds: string[]) => {
  if (sessionIds.length === 0) return Promise.resolve([] as BrowserSessionEventRecord[]);
  const qs = new URLSearchParams({ ids: sessionIds.join(","), since: "0" });
  return mcFetch<{ events: BrowserSessionEventRecord[] }>(
    `/api/v1/browser/sessions/events?${qs}`,
  ).then((r) => r.events);
};

export const terminateBrowserSession = (sessionId: string) =>
  mcFetch<{ session: BrowserSessionRecord }>(
    `/api/v1/browser/sessions/${encodeURIComponent(sessionId)}/terminate`,
    { method: "POST", body: "{}" },
  );

export const cancelBrowserSession = (sessionId: string) =>
  mcFetch<{ session: BrowserSessionRecord }>(
    `/api/v1/browser/sessions/${encodeURIComponent(sessionId)}/cancel`,
    { method: "POST", body: "{}" },
  );

export const closeBrowserSession = (sessionId: string) =>
  mcFetch<{ session: BrowserSessionRecord }>(
    `/api/v1/browser/sessions/${encodeURIComponent(sessionId)}/close`,
    { method: "POST", body: "{}" },
  );
