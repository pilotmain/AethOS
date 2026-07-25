/** Presence runtime — Mission Control API client. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type PresenceFeedEvent = {
  event_id?: string;
  summary?: string;
  source?: string;
  severity?: string;
  priority?: string;
  attention_score?: number;
  attention_reason?: string;
  confidence?: number;
  created_at?: number;
  dedupe_count?: number;
  deduplicated?: boolean;
  cluster_id?: string;
  context_weight?: number;
  signal_class?: string;
};

export type PresenceCluster = {
  cluster_id?: string;
  theme?: string;
  title?: string;
  event_count?: number;
  confidence?: number;
  sources?: string[];
  providers?: string[];
  related_systems?: string[];
  timeline?: { at?: number; summary?: string }[];
};

export type PresenceRecommendation = {
  recommendation_id?: string;
  title?: string;
  suggested_action?: string;
  operator_rationale?: string;
  governance_statement?: string;
  confidence?: number;
  severity?: string;
  approval_required?: boolean;
};

export type AttentionQuality = {
  priority_distribution?: Record<string, number>;
  urgency_inflation_ratio?: number;
  high_signal_count?: number;
  passive_count?: number;
};

export type PresenceState = {
  ok: boolean;
  feed?: PresenceFeedEvent[];
  attention?: PresenceFeedEvent[];
  clusters?: PresenceCluster[];
  incidents?: PresenceCluster[];
  recommendations?: PresenceRecommendation[];
  attention_quality?: AttentionQuality;
  focus?: { mode?: string; investigation?: string };
  memory?: Record<string, unknown>;
  watchers?: { watcher_id?: string; target?: string; status?: string }[];
  timelines?: { timeline_id?: string; entry_count?: number }[];
  autonomous_execution_blocked?: boolean;
};

export const fetchPresenceState = (sessionId = "default") =>
  mcFetch<PresenceState>(`/api/v1/presence/state?session_id=${encodeURIComponent(sessionId)}`);

export const fetchPresenceFeed = () =>
  mcFetch<{
    ok: boolean;
    feed?: PresenceFeedEvent[];
    attention?: PresenceFeedEvent[];
    clusters?: PresenceCluster[];
    attention_quality?: AttentionQuality;
  }>("/api/v1/presence/feed");

export const fetchPresenceAttention = () =>
  mcFetch<{ ok: boolean; attention?: PresenceFeedEvent[]; attention_quality?: AttentionQuality }>(
    "/api/v1/presence/attention"
  );

export const fetchPresenceClusters = () =>
  mcFetch<{ ok: boolean; clusters?: PresenceCluster[] }>("/api/v1/presence/clusters");

export const fetchPresenceIncidents = () =>
  mcFetch<{ ok: boolean; incidents?: PresenceCluster[]; clusters?: PresenceCluster[] }>(
    "/api/v1/presence/incidents"
  );

export const fetchIntelligentRecommendations = () =>
  mcFetch<{ ok: boolean; recommendations?: PresenceRecommendation[] }>(
    "/api/v1/presence/recommendations/intelligent"
  );

export const fetchAttentionQuality = () =>
  mcFetch<{ ok: boolean; attention?: PresenceFeedEvent[]; attention_quality?: AttentionQuality }>(
    "/api/v1/presence/attention/quality"
  );

export const fetchPresenceTimeline = (windowHours = 48) =>
  mcFetch<{ ok: boolean; timeline?: { timeline_id?: string; entries?: unknown[] } }>(
    `/api/v1/presence/timeline?window_hours=${windowHours}`
  );

export const fetchPresenceFocus = () =>
  mcFetch<{ ok: boolean; focus?: PresenceState["focus"]; sessions?: unknown[] }>("/api/v1/presence/focus");

export const fetchPresenceWatchers = () =>
  mcFetch<{ ok: boolean; watchers?: PresenceState["watchers"] }>("/api/v1/presence/watchers");

export const fetchPresenceMemory = () =>
  mcFetch<{ ok: boolean; memory?: Record<string, unknown> }>("/api/v1/presence/memory");

export const runPresenceCycle = () => mcFetch<{ ok: boolean }>("/api/v1/presence/cycle", { method: "POST" });

export const registerWatcher = (target: string) =>
  mcFetch<{ ok: boolean; watcher?: unknown }>("/api/v1/presence/watch", {
    method: "POST",
    body: JSON.stringify({ target }),
  });

export const dismissPresenceRecommendation = (id: string) =>
  mcFetch<{ ok: boolean }>(`/api/v1/presence/recommendation/${id}/dismiss`, { method: "POST" });

export const snoozePresenceRecommendation = (id: string, hours = 4) =>
  mcFetch<{ ok: boolean }>(`/api/v1/presence/recommendation/${id}/snooze`, {
    method: "POST",
    body: JSON.stringify({ hours }),
  });
