/** Mission Control — web intelligence / research artifacts API. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ResearchArtifact = {
  artifact_id: string;
  artifact_type: string;
  intent: string;
  source_url?: string | null;
  evidence_source?: string | null;
  channel?: string;
  confidence?: string;
  created_at?: number;
  payload?: Record<string, unknown>;
};

export type ResearchStatus = {
  enabled: boolean;
  provider: string;
  api_key_configured: boolean;
  api_key_preview?: string | null;
  max_results: number;
  artifacts_dir: string;
  configured: boolean;
  config_source: string;
  restart_required_hint?: string;
  errors: string[];
  loaded?: Record<string, string | number | boolean>;
};

export type ResearchReplay = {
  artifact_id: string;
  artifact_type: string;
  payload?: {
    replay_id?: string;
    query?: string;
    timeline?: { at?: number; step?: string; detail?: string }[];
    artifact_ids?: string[];
    plan?: Record<string, unknown>;
  };
};

export type ResearchProviderInfo = {
  provider_id: string;
  role: string;
  status: string;
};

export const fetchResearchProviders = () =>
  mcFetch<{ providers: ResearchProviderInfo[]; count: number }>("/api/v1/research/providers");

export const postResearchQuery = (message: string, sessionId = "default") =>
  mcFetch<{ ok: boolean; replay_id: string; reply: string; artifact_ids: string[]; timeline: unknown[] }>(
    "/api/v1/research/query",
    { method: "POST", body: JSON.stringify({ message, session_id: sessionId, channel: "mc" }) },
  );

export const fetchResearchReplay = (replayId: string) =>
  mcFetch<{ replay: ResearchReplay }>(`/api/v1/research/replay/${encodeURIComponent(replayId)}`);

export const fetchResearchStatus = () => mcFetch<ResearchStatus>("/api/v1/research/status");

export const fetchResearchArtifacts = (limit = 30) =>
  mcFetch<{ artifacts: ResearchArtifact[]; count: number }>(`/api/v1/research/artifacts?limit=${limit}`);
